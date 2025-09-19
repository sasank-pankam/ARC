import React from "react";
import GraphViewer from "./GraphViewer";
import NodeDetails from "./NodeDetails";
import { useNavigate } from "react-router-dom";
import FeedbackPage from "./FeedbackPage";

const GraphDetail = ({
        graphId,
        graph,
        onBack,
        onNodeClick,
        selectedNodeData,
}) => {
        const navigate = useNavigate();
        const [showFeedback, setShowFeedback] = React.useState(false);
        const handleDeleteGraph = async () => {
                try {
                        const response = await fetch(
                                `http://localhost:8080/batch?group_id=${encodeURIComponent(graphId)}`,
                                {
                                        method: "DELETE",
                                },
                        );
                        if (response.ok) {
                                if (typeof window !== "undefined" && window.toast) {
                                        window.toast.success("Batch deleted successfully");
                                }
                                if (typeof window !== "undefined" && window.dispatchEvent) {
                                        window.dispatchEvent(
                                                new CustomEvent("batchDeleted", { detail: { graphId } }),
                                        );
                                }
                                if (onBack) onBack();
                        } else {
                                if (typeof window !== "undefined" && window.toast) {
                                        window.toast.error("Failed to delete batch");
                                }
                        }
                } catch (err) {
                        if (typeof window !== "undefined" && window.toast) {
                                window.toast.error("Error deleting batch");
                        }
                }
        };

        return (
                <div className="graph-detail">
                        <div
                                className="graph-detail-header"
                                style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}
                        >
                                <button className="back-btn" onClick={onBack}>
                                        ← Back to Graphs
                                </button>
                                <div className="graph-info" style={{ flex: 1 }}>
                                        <p>Graph: {graphId}</p>
                                        <div className="graph-meta">
                                                <span>Alerts: {graph.nodes.length}</span>&nbsp;
                                                <span>Edges: {graph.edges.length}</span>&nbsp;
                                                <span>Created: {new Date(graph.createdAt).toLocaleString()}</span>
                                        </div>
                                </div>
                                <button
                                        className="feedback-btn"
                                        onClick={() => setShowFeedback(true)}
                                        style={{
                                                background: "#10b981",
                                                color: "white",
                                                border: "none",
                                                borderRadius: "6px",
                                                padding: "0.375rem 0.75rem",
                                                fontSize: "0.7rem",
                                                cursor: "pointer",
                                                marginRight: "0.5rem",
                                        }}
                                >
                                        Feedback
                                </button>
                                <button
                                        className="delete-btn"
                                        onClick={handleDeleteGraph}
                                        style={{
                                                background: "#dc2626",
                                                color: "white",
                                                border: "none",
                                                borderRadius: "6px",
                                                padding: "0.375rem 0.75rem",
                                                fontSize: "0.7rem",
                                                cursor: "pointer",
                                        }}
                                >
                                        Delete Batch
                                </button>
                        </div>

                        <div className="graph-detail-content">
                                <div className="graph-viewer-section">
                                        <GraphViewer
                                                graphId={graphId}
                                                nodes={graph.nodes}
                                                edges={graph.edges}
                                                onNodeClick={onNodeClick}
                                                selectedNodeData={selectedNodeData}
                                                isNewNode={graph.nodes.some((node) => node.data.isNew)}
                                                isNewEdge={graph.edges.some((edge) => edge.data.isNew)}
                                        />
                                </div>

                                <div className="node-details-section">
                                        <NodeDetails nodeData={selectedNodeData} />
                                </div>
                        </div>
                        {showFeedback && (
                                <div
                                        style={{
                                                position: "fixed",
                                                top: 0,
                                                left: 0,
                                                width: "100vw",
                                                height: "100vh",
                                                background: "rgba(30,41,59,0.18)",
                                                zIndex: 1000,
                                                display: "flex",
                                                alignItems: "center",
                                                justifyContent: "center",
                                        }}
                                >
                                        <div style={{ position: "relative", zIndex: 1001 }}>
                                                <FeedbackPage
                                                        graphId={graphId}
                                                        graph={graph}
                                                        onClose={() => setShowFeedback(false)}
                                                />
                                                <button
                                                        onClick={() => setShowFeedback(false)}
                                                        style={{
                                                                position: "absolute",
                                                                top: 25,
                                                                right: 10,
                                                                background: "#dc2626",
                                                                color: "#fff",
                                                                border: "none",
                                                                borderRadius: 6,
                                                                padding: "0.3rem 0.7rem",
                                                                fontSize: "0.9rem",
                                                                cursor: "pointer",
                                                                zIndex: 1002,
                                                        }}
                                                >
                                                        ✕
                                                </button>
                                        </div>
                                </div>
                        )}
                </div>
        );
};

export default GraphDetail;
