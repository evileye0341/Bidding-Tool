import unittest
from datetime import date

from streamlit.testing.v1 import AppTest


class AppFlowTests(unittest.TestCase):
    def test_pasted_requirements_survive_page_switches(self):
        app = AppTest.from_file("app.py")
        app.run(timeout=20)

        app.text_area[0].set_value("2 222\n3 333").run(timeout=20)

        first_day_button = next(
            button
            for button in app.button
            if button.key == "day_button_0"
        )
        self.assertIn("Req: 222", first_day_button.label)

        manual_nav_button = next(
            button
            for button in app.button
            if button.key == "nav_Manual Legality Checker"
        )
        manual_nav_button.click().run(timeout=20)

        generate_nav_button = next(
            button
            for button in app.button
            if button.key == "nav_Generate Bids"
        )
        generate_nav_button.click().run(timeout=20)

        first_day_button = next(
            button
            for button in app.button
            if button.key == "day_button_0"
        )
        self.assertIn("Req: 222", first_day_button.label)
        self.assertEqual(
            "2 222\n3 333",
            app.session_state["reserve_requirements_text_saved"]
        )

    def test_generated_bid_is_available_in_layer_builder(self):
        app = AppTest.from_file("app.py")
        app.run(timeout=20)

        generate_button = next(
            button
            for button in app.button
            if button.label == "Generate Legal Bids"
        )
        generate_button.click().run(timeout=30)

        use_bid_button = next(
            button
            for button in app.button
            if button.label == "Bid Now"
        )
        use_bid_button.click().run(timeout=30)

        self.assertIn("layer_bid_pattern", app.session_state)
        self.assertEqual("7-Layer Bid Builder", app.session_state["active_page"])
        self.assertTrue(
            any(
                message.value == "Bid #1 sent to 7-Layer Bid Builder."
                for message in app.success
            )
        )
        self.assertTrue(
            any(
                subheader.value == "Layer Sizes"
                for subheader in app.subheader
            )
        )
        self.assertFalse(
            any(
                info.value == "Choose a generated or manual bid first."
                for info in app.info
            )
        )

    def test_generated_bids_clear_when_setup_changes(self):
        app = AppTest.from_file("app.py")
        app.run(timeout=20)

        generate_button = next(
            button
            for button in app.button
            if button.label == "Generate Legal Bids"
        )
        generate_button.click().run(timeout=30)

        self.assertIn("last_generated_patterns", app.session_state)

        start_date_input = next(
            date_input
            for date_input in app.date_input
            if date_input.key == "start_date_input"
        )
        start_date_input.set_value(date(2026, 6, 3)).run(timeout=20)

        self.assertNotIn("last_generated_patterns", app.session_state)
        self.assertNotIn("layer_bid_pattern", app.session_state)

    def test_manual_bid_now_imports_bid_to_layer_builder(self):
        app = AppTest.from_file("app.py")
        app.run(timeout=20)

        manual_nav_button = next(
            button
            for button in app.button
            if button.key == "nav_Manual Legality Checker"
        )
        manual_nav_button.click().run(timeout=20)

        off_days = [3, 4, 5, 6, 10, 11, 12, 13, 17, 18, 22, 23]

        for idx in off_days:
            button = next(
                button
                for button in app.button
                if button.key == f"manual_day_button_{idx}"
            )
            button.click().run(timeout=30)

        bid_now_button = next(
            button
            for button in app.button
            if button.label == "Bid Now"
        )
        bid_now_button.click().run(timeout=30)

        self.assertIn("layer_bid_pattern", app.session_state)
        self.assertEqual("7-Layer Bid Builder", app.session_state["active_page"])
        self.assertTrue(
            any(
                subheader.value == "Layer Sizes"
                for subheader in app.subheader
            )
        )


if __name__ == "__main__":
    unittest.main()
