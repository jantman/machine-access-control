rfid_material_thickness = 0.111;
rfid_multipart_offset = 0.02; // should be comfortably larger than the kerf

rfid_top_tab_height = 0.368;
rfid_bottom_support_height = 0.52;

rfid_cover_plate_height = rfid_bottom_support_height + 3;

rfid_side_support_width = 0.52;
rfid_card_width = 2.125;
rfid_rfid_card_width_padding = 0.075;
rfid_card_cutout_width = rfid_card_width + rfid_rfid_card_width_padding;

rfid_fob_cutout_width = 1.3;
fob_cutout_depth = 1.4;
rfid_fob_slot_width = 0.375;

rfid_overall_width = rfid_card_cutout_width + (rfid_side_support_width * 2);
rfid_overall_height = rfid_top_tab_height + rfid_cover_plate_height;

rfid_mounting_hole_dia = 0.173; // clearance for M4 screws
