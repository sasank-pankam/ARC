import asyncio
from collections import defaultdict
from datetime import datetime, timedelta


from src.models import AlertGroup, FeedBack
from src.storage import BaseAlertStore
from . import BaseDetector, log
from src.message_queue import BaseMessageQueue
from src.graph import BaseGraph
from src.notifier import BaseNotifier
from src.models import Alert
from src.config import cfg

td = timedelta(minutes=cfg.detector.time_delta)


class AlertBatch:
    """Maintains a sliding window batch of alerts and their causal links."""

    def __init__(
        self,
        graph: BaseGraph,
        store: BaseAlertStore,
        notifier: BaseNotifier,
        links: dict,
        trigger_delete=lambda x: None,
    ):
        self.service_graph = graph
        self.store = store
        self.notifier = notifier
        self.deleter = trigger_delete

        self.links = links

        self.lower_bound: datetime = None
        self.upper_bound: datetime = None

        self.curr_alerts = set()  # set[Alert]
        self.service_to_alert: dict[int, set[Alert]] = defaultdict(set)
        self.notify_tasks: dict[int, asyncio.Task] = {}
        self.groups: list[AlertGroup] = []

    def check_temporal(self, alert: Alert):
        if self.lower_bound:
            if not (self.lower_bound - td <= alert.startsAt <= self.upper_bound + td):
                return False
        return True

    async def check_and_add_alert(self, alert: Alert):
        temporality = self.check_temporal(alert)
        log.debug(
            f"temporal check for alert {alert.id} {'passed' if temporality else 'falied'}"
        )
        if not temporality:
            return False

        linked = False

        if alert.service in self.service_to_alert and len(
            self.service_to_alert[alert.service]
        ):
            log.debug("Found same service is having an alert.")
            for o_alert in self.service_to_alert[alert.service]:
                linked = True
                if (o_alert.id, alert.id) not in self.links:
                    self.links[(o_alert.id, alert.id)] = [
                        cfg.detector.initial_alpha,
                        cfg.detector.initial_beta,
                    ]
                if (alert.id, o_alert.id) not in self.links:
                    self.links[(alert.id, o_alert.id)] = [
                        cfg.detector.initial_alpha,
                        cfg.detector.initial_beta,
                    ]

        parents = self.service_graph.get_connected(alert.service)
        children = self.service_graph.get_connected_down(alert.service)

        for p in parents:
            for p_alert in self.service_to_alert[p.id]:
                linked = True
                if (p_alert.id, alert.id) not in self.links:
                    self.links[(p_alert.id, alert.id)] = [
                        cfg.detector.initial_alpha,
                        cfg.detector.initial_beta,
                    ]
        if linked:
            log.debug("Found a parent for this alert.")

        for c in children:
            for c_alert in self.service_to_alert[c.id]:
                linked = True
                if (alert.id, c_alert.id) not in self.links:
                    self.links[(alert.id, c_alert.id)] = [
                        cfg.detector.initial_alpha,
                        cfg.detector.initial_beta,
                    ]

        if not linked:
            log.debug("No links found")
            return False

        log.debug("links found")

        self.curr_alerts.add(alert.id)
        self.service_to_alert[alert.service].add(alert)

        if not self.lower_bound:
            self.lower_bound = self.upper_bound = alert.startsAt
        else:
            self.lower_bound = min(self.lower_bound, alert.startsAt)
            self.upper_bound = max(self.upper_bound, alert.startsAt)

        await self.handle_this_alert(alert)
        return True

    async def handle_this_alert(self, alert: Alert):
        children = []
        parents = []
        for link, vals in self.links.items():
            if alert.id not in link:
                continue

            a, b = link
            if a == alert.id and b in self.curr_alerts:
                children.append(b)

            if b == alert.id and a in self.curr_alerts:
                parents.append(a)

        # if this has no parent then this may be a root
        # even if its not then the current alert can be a link to 2 seperate groups

        have_poked_a_child = False
        best_strenght = -float("inf")
        best_child = None
        for child in children:
            decision, strength = await self.get_strength(alert.id, child)
            log.debug(f"Child: {decision=}, {strength=} for ({alert.id}, {child})")

            if decision:
                if best_strenght < strength:
                    best_strenght = strength
                    best_child = child
                have_poked_a_child = True

        have_poked_a_parent = False
        best_strenght = -float("inf")
        best_parent = None
        for parent in parents:
            decision, strength = await self.get_strength(parent, alert.id)
            log.debug(f"Parent: {decision=}, {strength=} for ({parent}, {alert.id})")
            if decision:
                have_poked_a_parent = True
                if best_strenght < strength:
                    best_strenght = strength
                    best_parent = parent

        # in the further iterations add a case where the strength delta
        # is betweeen them in the less then add multiple childs for the current root.

        # special case:
        # here we need to check weather the child have any other parent.
        # if it have more link strength. then skip to only parent
        if have_poked_a_child and have_poked_a_parent:
            if await self.check_for_other_parents(alert.id, best_child):
                have_poked_a_child = False

        if have_poked_a_child and have_poked_a_parent:
            # assuming both parents and children
            # for now only considering best child and best parent.
            # bridge this alert between them

            log.debug("found both parent and child.")

            p_alert, _ = await self.store.get(best_parent)
            c_alert, _ = await self.store.get(best_child)

            alert.group = p_alert.group

            alert.parent_id = p_alert.id
            c_alert.parent_id = alert.id

            parent_grp: AlertGroup = p_alert.group
            child_grp: AlertGroup = c_alert.group

            log.debug(f"connecting {c_alert.id} to {p_alert.id}")

            for c_al in child_grp.group:  # convert the childs group to this group
                parent_grp.add_other(c_al)
                c_al.group = parent_grp
            parent_grp.add_other(alert)
            child_grp.group.clear()  # remove all alerts pointing to it

        elif have_poked_a_child:  # assuming no parent but a possible child
            # here we need to check weather the child have any other parent. then check for the.

            log.debug("found only children.")
            # add to childs grp replacing the child as root
            c_alert, _ = await self.store.get(best_child)

            log.debug(f"the best alert child for the {alert.id} is {best_child}")
            if best_child in self.notify_tasks:
                tsk = self.notify_tasks.get(best_child)
                tsk.cancel()

            grp = c_alert.group
            alert.group = grp
            c_alert.parent_id = alert.id

            grp.add_root(alert)
            self.register_as_a_root(alert)
        elif have_poked_a_parent:  # assuming no child but a parent
            log.debug("found only parent.")
            # add to parents grp without replacing any thing
            log.debug(f"the best alert parent for the {alert.id} is {best_parent}")
            p_alert, _ = await self.store.get(best_parent)
            grp: AlertGroup = p_alert.group

            alert.group = grp
            alert.parent_id = p_alert.id
            print(alert.id, alert)
            grp.add_other(alert)
        else:
            # assuming no child and no parent
            # create a new group
            log.debug("found no child and parent with strong enough link.")
            new_grp = AlertGroup(alert)

            alert.group = new_grp
            self.groups.append(new_grp)
            self.register_as_a_root(alert)
            return

    async def check_for_other_parents(self, curr_id, child_id):
        _, curr_strength = await self.get_strength(curr_id, child_id)
        for a, b in self.links.keys():
            if b != child_id:
                continue

            _, other_strenght = await self.get_strength(a, b)
            if curr_strength < other_strenght:
                return True

        return False

    def register_as_a_root(self, alert: Alert):
        log.debug(f"registering {alert.id} as root")
        tsk = self.notify_tasks.get(alert.id, None)
        if tsk:
            tsk.cancel()
        grp: AlertGroup = alert.group
        new_tsk = asyncio.create_task(
            self._notify_after_delay(grp.add_root(alert))
        )  # change this to new task that registered as wait time and send the request.
        self.notify_tasks[alert.id] = new_tsk

    async def get_strength(self, parent_id: int, child_id: int) -> tuple[bool, float]:
        alpha, beta_ = self.links.get(
            (parent_id, child_id),
            (cfg.detector.initial_alpha, cfg.detector.initial_beta),
        )
        total = (await self.store.get(child_id))[1]

        strength = alpha / total

        should = strength >= cfg.detector.confidence_threshold
        return should, strength

    async def _notify_after_delay(self, group: AlertGroup):
        root = group.root
        try:
            await asyncio.sleep(cfg.detector.delay)
            log.info(f"Notifying root={root.id} for {len(group.group)} alerts")
            await self.notifier.notify(group)
            self.groups.remove(group)
            if len(self.groups) == 0:
                self.deleter(self)
        except asyncio.CancelledError:
            log.debug(
                f"Notify task cancelled for group with root {str(group.root.id)} (new alert arrived)."
            )


class ProbabilityDetector(BaseDetector):
    """
    Learns causal link strengths with on-the-fly feedback.
    """

    def __init__(
        self,
        graph: BaseGraph,
        work_queue: BaseMessageQueue,
        store: BaseAlertStore,
        notifier: BaseNotifier,
        precomputed_links=None,
    ):
        super().__init__(graph, work_queue, store, notifier)

        self.links = precomputed_links or defaultdict(
            lambda: [cfg.detector.initial_alpha, cfg.detector.initial_beta]
        )
        self.batches: list[AlertBatch] = []

    async def process_alert(self, alert: Alert):
        log.debug(f"Processing alert {alert.id} {alert.service_name} {alert.summary}")
        for batch in self.batches:
            if await batch.check_and_add_alert(alert):
                log.debug("added alert to an already present batch.")
                alert.batch = batch
                return

        log.debug(
            "Creating new batch because the alert is not linkable to other batches."
        )

        new_batch = AlertBatch(
            self.service_graph,
            self.store,
            self.notifier,
            self.links,
            self.trigger_delete,
        )
        new_batch.curr_alerts.add(alert.id)
        new_batch.service_to_alert[alert.service].add(alert)
        alert.batch = new_batch
        alert.group = AlertGroup(alert)
        new_batch.register_as_a_root(alert)
        self.batches.append(new_batch)

    async def feedback_handler(self, fb: FeedBack):
        for (cause, effect), confirmed in fb.relations.items():
            key = (cause, effect)
            alpha, beta_ = self.links[key]
            if confirmed:
                alpha += 1  # one more success
            else:
                beta_ += 10  # aggressively reduce the strength.
            self.links[key] = [alpha, beta_]
            log.debug(f"Updating link with {key=} by {alpha=}, {beta_}")

        log.info("Causal link counts updated from feedback.")

    def trigger_delete(self, ag: AlertBatch):
        log.debug(f"deleting AlertGroup with root as {ag}")
        ind = self.batches.index(ag)
        if ind != -1:
            self.batches.pop(ind)
