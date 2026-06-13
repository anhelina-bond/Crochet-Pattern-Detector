import unittest

from llm_modifier import execute_operations, validate_graph


def make_sample_graph():
    return validate_graph(
        {
            "nodes": [
                {"id": 0, "x": 0.3, "y": 0.2, "w": 0.05, "h": 0.05, "type": "sc_stitch", "angle": 0},
                {"id": 1, "x": 0.7, "y": 0.21, "w": 0.05, "h": 0.05, "type": "hdc_stitch", "angle": 0},
                {"id": 2, "x": 0.3, "y": 0.52, "w": 0.05, "h": 0.05, "type": "dc_stitch", "angle": 0},
                {"id": 3, "x": 0.7, "y": 0.53, "w": 0.05, "h": 0.05, "type": "tr_stitch", "angle": 0},
            ],
            "edges": [
                {"child_id": 0, "parent_id": 2, "connection_type": "standard"},
                {"child_id": 1, "parent_id": 3, "connection_type": "standard"},
            ],
        }
    )


class LlmModifierTests(unittest.TestCase):
    def test_set_type_all_nodes(self):
        graph = execute_operations(
            make_sample_graph(),
            [{"operation": "set_type", "selector": {"scope": "all"}, "stitch_type": "dc_stitch"}],
        )

        self.assertTrue(all(node.type == "dc_stitch" for node in graph.nodes))

    def test_add_one_node_above_top_row(self):
        graph = execute_operations(
            make_sample_graph(),
            [
                {
                    "operation": "add_relative_nodes",
                    "selector": {"row": "top"},
                    "count": 1,
                    "stitch_type": "sc_stitch",
                    "placement": "above",
                    "connect_to_anchor": True,
                }
            ],
        )

        self.assertEqual(len(graph.nodes), 6)
        self.assertEqual(len(graph.edges), 4)
        self.assertLess(graph.nodes[4].y, graph.nodes[0].y)
        self.assertLess(graph.nodes[5].y, graph.nodes[1].y)

    def test_add_two_stacked_nodes_above_each_top_row_node(self):
        graph = execute_operations(
            make_sample_graph(),
            [
                {
                    "operation": "add_relative_nodes",
                    "selector": {"row": "top"},
                    "count": 2,
                    "stitch_type": "sc_stitch",
                    "placement": "above",
                    "connect_to_anchor": True,
                }
            ],
        )

        self.assertEqual(len(graph.nodes), 8)
        self.assertEqual(len(graph.edges), 6)
        self.assertAlmostEqual(graph.nodes[4].x, graph.nodes[0].x, places=4)
        self.assertAlmostEqual(graph.nodes[5].x, graph.nodes[0].x, places=4)
        self.assertAlmostEqual(graph.nodes[6].x, graph.nodes[1].x, places=4)
        self.assertAlmostEqual(graph.nodes[7].x, graph.nodes[1].x, places=4)
        self.assertNotAlmostEqual(graph.nodes[4].y, graph.nodes[5].y, places=3)
        self.assertNotAlmostEqual(graph.nodes[6].y, graph.nodes[7].y, places=3)
        self.assertTrue(all(0 <= node.x <= 1 and 0 <= node.y <= 1 for node in graph.nodes))
        self.assertEqual([node.id for node in graph.nodes], list(range(len(graph.nodes))))
        self.assertTrue(all(node.type == "sc_stitch" for node in graph.nodes[4:]))

    def test_horizontal_spread_still_available_when_requested(self):
        graph = execute_operations(
            make_sample_graph(),
            [
                {
                    "operation": "add_relative_nodes",
                    "selector": {"row": "top"},
                    "count": 2,
                    "stitch_type": "sc_stitch",
                    "placement": "above",
                    "distribution": "horizontal_spread",
                    "spread": 1.0,
                    "connect_to_anchor": True,
                }
            ],
        )

        self.assertLess(graph.nodes[4].x, graph.nodes[0].x)
        self.assertGreater(graph.nodes[5].x, graph.nodes[0].x)
        self.assertLess(graph.nodes[6].x, graph.nodes[1].x)
        self.assertGreater(graph.nodes[7].x, graph.nodes[1].x)

    def test_removes_invalid_edges_and_keeps_contiguous_ids(self):
        graph = validate_graph(
            {
                "nodes": [
                    {"id": 5, "x": 0.2, "y": 0.2, "type": "sc_stitch"},
                    {"id": 8, "x": 0.8, "y": 0.8, "type": "dc_stitch"},
                ],
                "edges": [
                    {"child_id": 5, "parent_id": 8, "connection_type": "standard"},
                    {"child_id": 99, "parent_id": 8, "connection_type": "standard"},
                ],
            }
        )

        repaired = execute_operations(graph, [])

        self.assertEqual([node.id for node in repaired.nodes], [0, 1])
        self.assertEqual(len(repaired.edges), 1)
        self.assertEqual(repaired.edges[0].child_id, 0)
        self.assertEqual(repaired.edges[0].parent_id, 1)


if __name__ == "__main__":
    unittest.main()
