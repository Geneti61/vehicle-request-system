                    # Build driver-name and plate lists
                    driver_names = ["— Select Driver —"] + [d.split(" - ")[0] for d in selectable]
                    plate_numbers = ["— Select Plate —"] + [d.split(" - ")[-1] for d in selectable]
                    name_to_plate = {d.split(" - ")[0]: d.split(" - ")[-1] for d in selectable}
                    plate_to_name = {d.split(" - ")[-1]: d.split(" - ")[0] for d in selectable}

                    col1, col2, col3 = st.columns([3, 3, 1])
                    with col1:
                        chosen_name = st.selectbox(
                            "Driver Name",
                            options=driver_names,
                            key=f"drvname_{r['request_id']}_{idx}",
                        )
                    with col2:
                        default_plate = "— Select Plate —"
                        if chosen_name != "— Select Driver —":
                            default_plate = name_to_plate.get(chosen_name, "— Select Plate —")
                        plate_index = plate_numbers.index(default_plate) if default_plate in plate_numbers else 0
                        chosen_plate = st.selectbox(
                            "Plate Number",
                            options=plate_numbers,
                            index=plate_index,
                            key=f"plate_{r['request_id']}_{idx}",
                        )
                    with col3:
                        st.write("")
                        st.write("")
                        assign_clicked = st.button(
                            "✅ Assign",
                            key=f"assign_{r['request_id']}_{idx}",
                            use_container_width=True,
                        )

                    # Resolve final driver + plate
                    final_driver = ""
                    final_plate = ""
                    if chosen_name != "— Select Driver —":
                        final_driver = chosen_name
                        final_plate = name_to_plate.get(chosen_name, "")
                    elif chosen_plate != "— Select Plate —":
                        final_plate = chosen_plate
                        final_driver = plate_to_name.get(chosen_plate, "")
