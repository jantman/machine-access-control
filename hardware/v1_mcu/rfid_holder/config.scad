material_thickness = 0.111;
multipart_offset = 0.02; // should be comfortably larger than the kerf

top_tab_height = 0.368;
bottom_support_height = 0.52;

cover_plate_height = bottom_support_height + 3;

side_support_width = 0.52;
card_width = 2.125;
card_width_padding = 0.075;
card_cutout_width = card_width + card_width_padding;

fob_cutout_width = 1.3;
fob_cutout_depth = 1.4;
fob_slot_width = 0.375;

overall_width = card_cutout_width + (side_support_width * 2);
overall_height = top_tab_height + cover_plate_height;

mounting_hole_dia = 0.173; // clearance for M4 screws
