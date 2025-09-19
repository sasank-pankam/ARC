import React, { useState, useEffect } from "react";
import { toast, Toaster } from "react-hot-toast";
import GraphList from "./GraphList";
import GraphDetail from "./GraphDetail";
import TestControls from "./TestControls";
import websocketService from "../services/websocketService";

const Dashboard = () => {
        const [graphs, setGraphs] = useState({});
        const [selectedNodeData, setSelectedNodeData] = useState(null);
        const [connectionStatus, setConnectionStatus] = useState("disconnected");
        const [showTestControls, setShowTestControls] = useState(false);
        const [selectedGraphId, setSelectedGraphId] = useState(null);

        useEffect(() => {
                // Connect to WebSocket
                websocketService.onConnectCallback = () => {
                        setConnectionStatus("connected");
                };
                websocketService.connect();
                setConnectionStatus("connecting");

                // Set up message handler
                websocketService.setMessageCallback(handleWebSocketMessage);

                // Expose toast globally for GraphList
                window.toast = toast;

                // Listen for batchDeleted event
                const handleBatchDeleted = (e) => {
                        const { graphId } = e.detail;
                        setGraphs((prev) => {
                                const newGraphs = { ...prev };
                                delete newGraphs[graphId];
                                return newGraphs;
                        });
                };
                window.addEventListener("batchDeleted", handleBatchDeleted);

                return () => {
                        websocketService.disconnect();
                        window.removeEventListener("batchDeleted", handleBatchDeleted);
                };
        }, []);

        // Expose graphs on window for FeedbackPage
        React.useEffect(() => {
                if (typeof window !== "undefined") {
                        window.graphs = graphs;
                }
        }, [graphs]);

        const handleWebSocketMessage = (message) => {
                handleCreateGraph(message);
        };

        const handleCreateGraph = (message) => {
                const { group_id: graph_id, alerts } = message;

                console.log("Processing graph creation with alerts:", alerts);

                // Process alerts to create nodes and edges
                const nodes = [];
                const edges = [];
                const processedNodes = new Set();

                // First pass: create all nodes
                alerts.forEach((alert) => {
                        const nodeData = {
                                id: alert.id,
                                label: alert.service || `Alert ${alert.id}`,
                                parentId: alert.parent_id || null,
                                isRoot: !alert.parent_id || alert.parent_id === "", // Root if no parent_id or empty string
                                timestamp: new Date().toISOString(),
                                properties: {
                                        service: alert.service,
                                        summary: alert.summary,
                                },
                                metadata: {
                                        original_alert: alert,
                                },
                        };

                        nodes.push({
                                data: {
                                        ...nodeData,
                                        isNew: true, // Flag for animation
                                },
                        });

                        processedNodes.add(alert.id);
                });

                // Second pass: create edges based on parent-child relationships
                alerts.forEach((alert) => {
                        if (
                                alert.parent_id &&
                                alert.parent_id !== "" &&
                                processedNodes.has(alert.parent_id)
                        ) {
                                const edgeData = {
                                        source: alert.parent_id,
                                        target: alert.id,
                                        timestamp: new Date().toISOString(),
                                };

                                edges.push({
                                        data: {
                                                ...edgeData,
                                                isNew: true, // Flag for animation
                                        },
                                });
                        }
                });

                // Create the graph with all nodes and edges
                setGraphs((prevGraphs) => ({
                        ...prevGraphs,
                        [graph_id]: {
                                nodes: nodes,
                                edges: edges,
                                createdAt: new Date().toISOString(),
                        },
                }));

                toast.success(`New group detected`, {
                        duration: 3000,
                        position: "top-right",
                        style: {
                                background: "#e74c3c",
                                color: "#ffffff",
                                fontSize: "12px",
                                fontWeight: "500",
                                padding: "8px 12px",
                                borderRadius: "4px",
                                boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
                        },
                });

                // Remove animation flags after a delay
                setTimeout(() => {
                        setGraphs((prevGraphs) => {
                                const graph = prevGraphs[graph_id];
                                if (!graph) return prevGraphs;

                                return {
                                        ...prevGraphs,
                                        [graph_id]: {
                                                ...graph,
                                                nodes: graph.nodes.map((node) => ({
                                                        ...node,
                                                        data: { ...node.data, isNew: false },
                                                })),
                                                edges: graph.edges.map((edge) => ({
                                                        ...edge,
                                                        data: { ...edge.data, isNew: false },
                                                })),
                                        },
                                };
                        });
                }, 1000);
        };

        const handleNodeClick = (nodeData) => {
                setSelectedNodeData(nodeData);
        };

        const handleTestMessage = (message) => {
                // Simulate WebSocket message for testing
                handleWebSocketMessage(message);
        };

        const handleGraphSelect = (graphId) => {
                setSelectedGraphId(graphId);
                setSelectedNodeData(null); // Reset selected node when switching graphs
        };

        const handleBackToList = () => {
                setSelectedGraphId(null);
                setSelectedNodeData(null);
        };

        const getConnectionStatusColor = () => {
                switch (connectionStatus) {
                        case "connected":
                                return "#2ecc71";
                        case "connecting":
                                return "#f39c12";
                        case "disconnected":
                                return "#e74c3c";
                        default:
                                return "#95a5a6";
                }
        };

        return (
                <div className="dashboard">
                        <Toaster />

                        {/* Header */}
                        <div className="dashboard-header">
                                <h1>Root Cause Detector Dashboard</h1>
                                <div className="header-controls">
                                        <div className="connection-status">
                                                <span
                                                        className="status-indicator"
                                                        style={{ backgroundColor: getConnectionStatusColor() }}
                                                ></span>
                                                <span className="status-text">
                                                        {connectionStatus.charAt(0).toUpperCase() +
                                                                connectionStatus.slice(1)}
                                                </span>
                                        </div>
                                        <button
                                                className="test-toggle-btn"
                                                onClick={() => setShowTestControls(!showTestControls)}
                                        >
                                                {showTestControls ? "Hide" : "Show"} Test Controls
                                        </button>
                                </div>
                        </div>

                        {/* Test Controls */}
                        {showTestControls && (
                                <div className="test-controls-section">
                                        <TestControls onSendMessage={handleTestMessage} />
                                </div>
                        )}

                        {/* Main Content */}
                        <div className="dashboard-content">
                                {selectedGraphId ? (
                                        // Graph Detail View
                                        <GraphDetail
                                                graphId={selectedGraphId}
                                                graph={graphs[selectedGraphId]}
                                                onBack={handleBackToList}
                                                onNodeClick={handleNodeClick}
                                                selectedNodeData={selectedNodeData}
                                        />
                                ) : (
                                        // Graph List View
                                        <GraphList
                                                graphs={graphs}
                                                onGraphSelect={handleGraphSelect}
                                                selectedGraphId={selectedGraphId}
                                        />
                                )}
                        </div>
                </div>
        );
};

export default Dashboard;
