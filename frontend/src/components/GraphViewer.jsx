import React, { useRef, useEffect, useState } from "react";
import CytoscapeComponent from "react-cytoscapejs";
import cytoscape from "cytoscape";
import dagre from "cytoscape-dagre";

// Register the dagre layout
cytoscape.use(dagre);

const GraphViewer = ({
        graphId,
        nodes,
        edges,
        onNodeClick,
        selectedNodeData,
        isNewNode = false,
        isNewEdge = false,
}) => {
        const cyRef = useRef(null);
        const [cy, setCy] = useState(null);

        const styles = [
                {
                        selector: "node",
                        style: {
                                label: "data(label)",
                                "text-valign": "center",
                                "text-halign": "center",
                                "font-family": "Segoe UI, sans-serif",
                                "font-size": "8px",
                                color: "#333333",
                                "background-color": "white",
                                "border-color": "#cccccc",
                                "border-width": "1px",
                                shape: "roundrectangle",
                                width: "label",
                                height: "20px",
                                padding: "4px",
                        },
                },
                {
                        selector: "node[isRoot = 'true']",
                        style: {
                                "background-color": "#e74c3c ",
                                "border-color": "#000000 ",
                                "border-width": "1px ",
                                color: "#ffffff ",
                                "font-size": "9px",
                                width: "label",
                                height: "24px",
                        },
                },
                {
                        selector: "edge",
                        style: {
                                "curve-style": "bezier",
                                "target-arrow-shape": "triangle",
                                "target-arrow-color": "#ccc",
                                "line-color": "#aaa",
                                width: 1,
                                label: "data(label)",
                                "font-size": "7px",
                                color: "#777",
                                "text-margin-y": -6,
                        },
                },
                {
                        selector: "node.new-node",
                        style: {
                                "background-color": "#9b59b6",
                                "border-color": "#8e44ad",
                                "border-width": 2,
                                transform: "scale(1.2)",
                        },
                },
                {
                        selector: "edge.new-edge",
                        style: {
                                "line-color": "#9b59b6",
                                "target-arrow-color": "#9b59b6",
                                width: 3,
                                opacity: 0.8,
                        },
                },
        ];

        // Improved layout function using dagre for better hierarchical positioning
        const getLayout = () => {
                const rootNode = nodes.find((node) => node.data.isRoot);

                if (rootNode && nodes.length > 1) {
                        // Use dagre layout for better tree-like positioning
                        return {
                                name: "dagre",
                                rankDir: "TB", // Top to bottom
                                rankSep: 60,
                                nodeSep: 40,
                                padding: 30,
                                animate: false, // No layout animation
                                fit: true,
                                roots: `#${rootNode.data.id}`,
                        };
                } else if (nodes.length > 1) {
                        // Use breadthfirst for general graphs
                        return {
                                name: "breadthfirst",
                                directed: true,
                                padding: 30,
                                spacingFactor: 1.2,
                                animate: false, // No layout animation
                                fit: true,
                        };
                } else {
                        // Use grid for single nodes or empty graphs
                        return {
                                name: "grid",
                                padding: 30,
                                animate: false, // No layout animation
                                fit: true,
                        };
                }
        };

        useEffect(() => {
                if (cy) {
                        // Add click event listener
                        cy.on("tap", "node", (evt) => {
                                const node = evt.target;
                                const nodeData = node.data();
                                onNodeClick(nodeData);
                        });
                }
        }, [cy, onNodeClick]);

        useEffect(() => {
                if (cy && isNewNode) {
                        // Animate new nodes only when they're actually new
                        const newNodes = cy.nodes(".new-node");
                        newNodes.forEach((node) => {
                                node.animate(
                                        {
                                                style: { transform: "scale(1)" },
                                        },
                                        {
                                                duration: 1000,
                                                complete: () => {
                                                        node.removeClass("new-node");
                                                },
                                        },
                                );
                        });
                }
        }, [cy, isNewNode]);

        useEffect(() => {
                if (cy && isNewEdge) {
                        // Animate new edges only when they're actually new
                        const newEdges = cy.edges(".new-edge");
                        newEdges.forEach((edge) => {
                                edge.animate(
                                        {
                                                style: { opacity: 1 },
                                        },
                                        {
                                                duration: 1000,
                                                complete: () => {
                                                        edge.removeClass("new-edge");
                                                },
                                        },
                                );
                        });
                }
        }, [cy, isNewEdge]);

        const elements = CytoscapeComponent.normalizeElements({
                nodes: nodes.map((node) => {
                        // Debug logging
                        // console.log("Processing node in GraphViewer:", node.data);
                        // console.log("Node isRoot value:", node.data.isRoot);

                        const classes = [node.data.isNew ? "new-node" : ""]
                                .filter(Boolean)
                                .join(" ");

                        // console.log("Assigned classes:", classes);

                        const thing = {
                                ...node,
                                data: {
                                        ...node.data,
                                        // Convert boolean to string for CSS selector
                                        // Add classes for styling
                                        classes: classes,
                                        isRoot: node.data.isRoot ? "true" : "false",
                                        name: 1,
                                },
                        };
                        return thing;
                }),
                edges: edges.map((edge) => ({
                        ...edge,
                        data: {
                                ...edge.data,
                                // Add new-edge class for animation if it's a new edge
                                classes: edge.data.isNew ? "new-edge" : "",
                        },
                })),
        });

        console.log("Elements are: ", elements);

        return (
                <div className="graph-viewer">
                        <div className="graph-header">
                                <p>Graph: {graphId}</p>
                                <div className="graph-stats">
                                        <span>Nodes: {nodes.length}</span>&nbsp;
                                        <span>Edges: {edges.length}</span>&nbsp;
                                </div>
                        </div>
                        <CytoscapeComponent
                                ref={cyRef}
                                elements={elements}
                                style={{
                                        width: "100%",
                                        height: "600px",
                                        border: "1px solid #ddd",
                                        borderRadius: "8px",
                                        backgroundColor: "#f8f9fa",
                                }}
                                layout={getLayout()}
                                stylesheet={styles}
                                cy={(cyInstance) => setCy(cyInstance)}
                        />
                </div>
        );
};

export default GraphViewer;
