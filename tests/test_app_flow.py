import unittest

from streamlit.testing.v1 import AppTest


class AppFlowTests(unittest.TestCase):
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

    def test_manual_bid_now_imports_bid_to_layer_builder(self):
        app = AppTest.from_file("app.py")
        app.run(timeout=20)

        view_radio = next(
            radio
            for radio in app.radio
            if radio.label == "View"
        )
        view_radio.set_value("Manual Legality Checker").run(timeout=20)

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
