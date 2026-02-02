# This is an example plugin file.
# Users can create their own plugins by following this structure.

def on_cards_detected(cards_info, api):
    """
    This hook is called when the detector finishes processing a frame.
    
    :param cards_info: A list of detected card dictionaries.
                       Example: [{"card_id": "...", "name": "...", "position_on_screen": [...]}]
    :param api: A safe API object to interact with the main application.
                Example: api.overlay.draw_rect(...)
    """
    # Example: Print the name of the first detected card
    if cards_info:
        print(f"[ExamplePlugin] Detected card: {cards_info[0]['name']}")

    # Example: Draw a blue box on the first card
    if cards_info:
        pos = cards_info[0]['position_on_screen']
        api.overlay.draw_rect(pos[0], pos[1], pos[2], pos[3], color=(0, 0, 255, 128))

def on_game_state_changed(old_state, new_state, api):
    """
    This hook is called when the game state changes (e.g., from 'shop' to 'battle').
    
    :param old_state: The previous state string (e.g., 'shop').
    :param new_state: The new state string (e.g., 'battle').
    :param api: A safe API object.
    """
    print(f"[ExamplePlugin] Game state changed from {old_state} to {new_state}")

# You can add more hooks as the API expands.
# For example: on_log_line_read, on_battle_start, on_shop_enter, etc.
