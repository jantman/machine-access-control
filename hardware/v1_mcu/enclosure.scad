function inch(n) = n * 25.4;
function mm(n) = n;
function mm_inside_inch_scale(n) = n / 25.4;

use <esp32.scad>;
use <neopixel.scad>;
use <relay.scad>;
use <rfid.scad>;
use <esp32.scad>;
use <lcd.scad>;
use <rfid_holder/modules.scad>;
use <oops_button.scad>;
include <config.scad>;
include <dims.scad>;
include <rfid_holder/config.scad>;
include <./YAPPgenerator_v3.scad>;
use <fillets.scad>;

show_components = true;

// BEGIN dm-mac v1 MCU configuration

// BEGIN YAPP box config variables used in dm-mac custom code
wallThickness       = mm(4.0);
basePlaneThickness  = mm(4.0);
lidPlaneThickness   = mm(2.0);
pcbLength           = inch(8); // front to back (X axis)
pcbWidth            = inch(5); // side to side (Y axis)
paddingFront        = mm(2);
paddingBack         = mm(2);
paddingRight        = mm(2);
paddingLeft         = mm(2);
baseWallHeight      = inch(1.5);
lidWallHeight       = inch(0.25);
// END YAPP box config variables used in dm-mac custom code

lid_screw_dia = mm(3.2); // M3 screw clearance; M4 = 4.25
lid_insert_dia = mm(4.1); // M3 threaded insert; M4 = 4.9
lid_screw_head_dia = mm(7); // M3 flat head screw head diameter

rfid_holder_left_edge = pcbLength - inch(rfid_overall_width);
rfid_holder_translate = [rfid_holder_left_edge, ((pcbWidth - inch(rfid_overall_height)) / 2) + paddingFront];
rfid_reader_translate = [rfid_holder_translate[0] + ((inch(rfid_overall_width) - inch(1.030)) / 2), rfid_holder_translate[1] + (inch(rfid_cover_plate_height) - inch(fob_cutout_depth) - inch(0.425)), 0];
rfid_reader_board_thickness = inch(0.040);
rfid_reader_overall_height = inch(0.185);

lcd_width = inch(3.152);
lcd_translate = [(rfid_holder_left_edge - lcd_width) / 2, (pcbWidth / 3) + paddingFront + inch(lcd_centerline), 0];

oops_translate = [(rfid_holder_left_edge / 3) + paddingBack, (pcbWidth / 3) + paddingFront - (inch(0.625) / 2), 0];
neopixel_translate = [((rfid_holder_left_edge / 3) * 2) + paddingBack, (pcbWidth / 3) + paddingFront - (inch(0.321) / 2), 0];

//===========================================================
//-- origin = box(0,0,0)
module hookBaseCutouts()
{
  //if (printMessages) echo("hookBaseCutouts() ..");

} //-- hookBaseCutouts()

//===========================================================
//-- origin = box(0,0,0)
module hookLidCutouts()
{
  // mounting holes for RFID card/fob holder
  translate([rfid_holder_translate[0], rfid_holder_translate[1], 0]) {
    scale([25.4, 25.4, 25.4]) {
      rfid_holder_mounting_holes();
    }
  } // mounting holes for RFID card/fob holder
  // LCD display cutout
  translate([lcd_translate[0], lcd_translate[1], baseWallHeight + inch(lcd_display_depth)]) {
    scale([25.4, 25.4, 25.4]) {
      lcd();
    }
  } // LCD display cutout
  // Oops button
  translate([oops_translate[0], oops_translate[1], baseWallHeight - 10]) {
    cylinder(d=inch(0.645), h=20);
  } // Oops button
  // neopixel status LED
  translate([neopixel_translate[0], neopixel_translate[1], baseWallHeight - 10]) {
    cylinder(d=inch(0.301 + 0.020), h=20);
  } // neopixel status LED
} //-- hookLidCutouts()

module hookLidOutside() {
  include <rfid_holder/config.scad>;
  if(show_components) {
    // RFID card/fob holder
    translate([rfid_holder_translate[0], rfid_holder_translate[1], lidPlaneThickness]) {
      scale([25.4, 25.4, 25.4]) {
        bottom_layer();
        translate([0, 0, rfid_material_thickness]) {
            middle_layer();
        }
        translate([0, 0, rfid_material_thickness * 2]) {
            top_layer();
        }
      }
    } // RFID card/fob holder
    // Oops button
    translate([oops_translate[0], oops_translate[1], (baseWallHeight - 10) - inch(0.790+0.300)]) {
      scale([25.4, 25.4, 25.4]) {
        oops_button();
      }
    } // Oops button
    // neopixel status LED
    translate([neopixel_translate[0], neopixel_translate[1], baseWallHeight - 10 + inch(-1.38 + 0.301)]) {
      scale([25.4, 25.4, 25.4]) {
        neopixel();
      }
    } // neopixel status LED
  }
}

module hookLidInside()
{
  // RFID reader
  translate([rfid_reader_translate[0], rfid_reader_translate[1], (-1 * rfid_reader_overall_height) + 0]) {
    scale([25.4, 25.4, 25.4]) {
      translate([1.030, 0, 0]) {
        rotate([0, 0, 90]) {
          if(show_components) { translate([0, 0, -1 * mm_inside_inch_scale(rfid_reader_board_thickness)]) { rfid(); } } // show model if desired
          // mounting standoffs
          rfid_reader_hole_dia = 0.131;
          translate([0.137 + (rfid_reader_hole_dia/2), 1.030 - (0.140 + (rfid_reader_hole_dia/2)), 0]) {
              filleted_standoff(mm_inside_inch_scale(rfid_reader_overall_height), mm_inside_inch_scale(4), mm_inside_inch_scale(m3_minor), mm_inside_inch_scale(2), end="top");
          }
          translate([1.860 - (0.130 + (rfid_reader_hole_dia/2)), 0.132 + (rfid_reader_hole_dia/2), 0]) {
              filleted_standoff(mm_inside_inch_scale(rfid_reader_overall_height), mm_inside_inch_scale(4), mm_inside_inch_scale(m3_minor), mm_inside_inch_scale(2), end="top");
          }
          // END mounting standoffs
        } // rotate
      } // translate
    } // scale
  } // RFID reader
  // LCD display
  translate([lcd_translate[0], lcd_translate[1], -1 * inch(lcd_display_depth)]) {
    scale([25.4, 25.4, 25.4]) {
      if(show_components) { lcd(); }
      // BEGIN LCD mounting standoffs
      translate([lcd_hole_x_inset + (lcd_hole_dia / 2), lcd_hole_y_inset + lcd_hole_dia, 0]) {
        filleted_standoff(mm_inside_inch_scale(lcd_display_height), mm_inside_inch_scale(4), mm_inside_inch_scale(m3_minor), mm_inside_inch_scale(1), end="top");
      }
      translate([lcd_hole_x_inset + (lcd_hole_dia / 2), lcd_hole_y_inset + lcd_hole_dia + lcd_hole_y_spacing, 0]) {
        filleted_standoff(mm_inside_inch_scale(lcd_display_height), mm_inside_inch_scale(4), mm_inside_inch_scale(m3_minor), mm_inside_inch_scale(1), end="top");
      }
      translate([lcd_hole_x_inset + (lcd_hole_dia / 2) + lcd_hole_x_spacing, lcd_hole_y_inset + lcd_hole_dia, 0]) {
        filleted_standoff(mm_inside_inch_scale(lcd_display_height), mm_inside_inch_scale(4), mm_inside_inch_scale(m3_minor), mm_inside_inch_scale(1), end="top");
      }
      translate([lcd_hole_x_inset + (lcd_hole_dia / 2) + lcd_hole_x_spacing, lcd_hole_y_inset + lcd_hole_dia + lcd_hole_y_spacing, 0]) {
        filleted_standoff(mm_inside_inch_scale(lcd_display_height), mm_inside_inch_scale(4), mm_inside_inch_scale(m3_minor), mm_inside_inch_scale(1), end="top");
      }
      // END LCD mounting standoffs
    }
  } // LCD display
  // Oops button
  if(show_components) {
    translate([oops_translate[0], oops_translate[1], (baseWallHeight - 10) - inch(0.790+0.300)]) {
      scale([25.4, 25.4, 25.4]) {
        oops_button();
      }
    }
  } // Oops button
  // neopixel status LED
  if(show_components) {
    translate([neopixel_translate[0], neopixel_translate[1], baseWallHeight - 10 + inch(-0.301)]) {
      scale([25.4, 25.4, 25.4]) {
        neopixel();
      }
    }
  } // neopixel status LED
} //-- hookLidInside()

// END dm-mac v1 MCU configuration

module filleted_standoff(h, d, bore, fillet_width, end="bottom") {
  difference() {
    if(end == "bottom") {
      cylinder_fillet_outside(h=h, r=d/2, top=0, bottom=fillet_width, $fn=360, fillet_fn=360);
    } else {
      cylinder_fillet_outside(h=h, r=d/2, top=fillet_width, bottom=0, $fn=360, fillet_fn=360);
    }
    translate([0, 0, -0.1]) {
      cylinder(d=bore, h=h+1, $fn=360);
    }
  }
}

//---------------------------------------------------------
// This design is parameterized based on the size of a PCB.
//---------------------------------------------------------
// Note: length/lengte refers to X axis,
//       width/breedte refers to Y axis,
//       height/hoogte refers to Z axis

/*
      padding-back|<------pcb length --->|<padding-front
                            RIGHT
        0    X-axis --->
        +----------------------------------------+   ---
        |                                        |    ^
        |                                        |   padding-right
      Y |                                        |    v
      | |    -5,y +----------------------+       |   ---
 B    a |         | 0,y              x,y |       |     ^              F
 A    x |         |                      |       |     |              R
 C    i |         |                      |       |     | pcb width    O
 K    s |         |                      |       |     |              N
        |         | 0,0              x,0 |       |     v              T
      ^ |    -5,0 +----------------------+       |   ---
      | |                                        |    padding-left
      0 +----------------------------------------+   ---
        0    X-as --->
                          LEFT
*/


//-- which part(s) do you want to print?
printBaseShell        = true;
printLidShell         = true;
printSwitchExtenders  = false;
printDisplayClips     = false;

// ********************************************************************
// The Following will be used as the first element in the pbc array

//Defined here so you can define the "Main" PCB using these if wanted
pcbThickness        = mm(1.6);
standoffHeight      = mm(1.0); //-- How much the PCB needs to be raised from the base to leave room for solderings and whatnot
standoffDiameter    = mm(7);
standoffPinDiameter = mm(2.4);
standoffHoleSlack   = mm(0.4);

//===================================================================
// *** PCBs ***
// Printed Circuit Boards
//-------------------------------------------------------------------
//  Default origin =  yappCoordPCB : yappCoordBoxInside[0,0,0]
//
//  Parameters:
//   Required:
//    p(0) = name
//    p(1) = length
//    p(2) = width
//    p(3) = posx
//    p(4) = posy
//    p(5) = Thickness
//    p(6) = standoff_Height
//    p(7) = standoff_Diameter
//    p(8) = standoff_PinDiameter
//   Optional:
//    p(9) = standoff_HoleSlack (default to 0.4)

//The following can be used to get PCB values elsewhere in the script - not in pcb definition.
//If "PCB Name" is omitted then "Main" is used
//  pcbLength           --> pcbLength("PCB Name")
//  pcbWidth            --> pcbWidth("PCB Name")
//  pcbThickness        --> pcbThickness("PCB Name")
//  standoffHeight      --> standoffHeight("PCB Name")
//  standoffDiameter    --> standoffDiameter("PCB Name")
//  standoffPinDiameter --> standoffPinDiameter("PCB Name")
//  standoffHoleSlack   --> standoffHoleSlack("PCB Name")

pcb =
[
  // Default Main PCB - DO NOT REMOVE the "Main" line.
  ["Main",              pcbLength,pcbWidth,    0,0,    pcbThickness,  standoffHeight, standoffDiameter, standoffPinDiameter, standoffHoleSlack]
];

//-------------------------------------------------------------------
//-- padding between pcb and inside wall

//-- Total height of box = lidPlaneThickness
//                       + lidWallHeight
//--                     + baseWallHeight
//                       + basePlaneThickness
//-- space between pcb and lidPlane :=
//--      (bottonWallHeight+lidWallHeight) - (standoffHeight+pcbThickness)

//-- ridge where base and lid off box can overlap
//-- Make sure this isn't less than lidWallHeight
ridgeHeight         = mm(5.0);
ridgeSlack          = mm(0.2);
roundRadius         = mm(3.0);

// Box Types are 0-4 with 0 as the default
// 0 = All edges rounded with radius (roundRadius) above
// 1 = All edges sqrtuare
// 2 = All edges chamfered by (roundRadius) above
// 3 = Square top and bottom edges (the ones that touch the build plate) and rounded vertical edges
// 4 = Square top and bottom edges (the ones that touch the build plate) and chamfered vertical edges
// 5 = Chanfered top and bottom edges (the ones that touch the build plate) and rounded vertical edges
boxType             = 0; // Default type 0

// Set the layer height of your printer
printerLayerHeight  = mm(0.2);


//---------------------------
//--     C O N T R O L     --
//---------------------------
// -- Render --
renderQuality             = 8;          //-> from 1 to 32, Default = 8

// --Preview --
previewQuality            = 5;          //-> from 1 to 32, Default = 5
showSideBySide            = true;       //-> Default = true
onLidGap                  = 0;  // tip don't override to animate the lid opening
colorLid                  = "YellowGreen";
alphaLid                  = 1;
colorBase                 = "BurlyWood";
alphaBase                 = 1;
hideLidWalls              = false;      //-> Remove the walls from the lid : only if preview and showSideBySide=true
hideBaseWalls             = false;      //-> Remove the walls from the base : only if preview and showSideBySide=true
showOrientation           = true;       //-> Show the Front/Back/Left/Right labels : only in preview
showPCB                   = false;      //-> Show the PCB in red : only in preview
showSwitches              = false;      //-> Show the switches (for pushbuttons) : only in preview
showButtonsDepressed      = false;      //-> Should the buttons in the Lid On view be in the pressed position
showOriginCoordBox        = false;      //-> Shows red bars representing the origin for yappCoordBox : only in preview
showOriginCoordBoxInside  = false;      //-> Shows blue bars representing the origin for yappCoordBoxInside : only in preview
showOriginCoordPCB        = false;      //-> Shows blue bars representing the origin for yappCoordBoxInside : only in preview
showMarkersPCB            = false;      //-> Shows black bars corners of the PCB : only in preview
showMarkersCenter         = false;      //-> Shows magenta bars along the centers of all faces
inspectX                  = 0;          //-> 0=none (>0 from Back)
inspectY                  = 0;          //-> 0=none (>0 from Right)
inspectZ                  = 0;          //-> 0=none (>0 from Bottom)
inspectXfromBack          = true;       //-> View from the inspection cut foreward
inspectYfromLeft          = true;       //-> View from the inspection cut to the right
inspectZfromBottom        = true;       //-> View from the inspection cut up
//---------------------------
//--     C O N T R O L     --
//---------------------------

//-------------------------------------------------------------------
//-------------------------------------------------------------------
// Start of Debugging config (used if not overridden in template)
// ------------------------------------------------------------------
// ------------------------------------------------------------------

//==================================================================
//  *** Shapes ***
//------------------------------------------------------------------
//  There are a view pre defines shapes and masks
//  shapes:
//      shapeIsoTriangle, shapeHexagon, shape6ptStar
//
//  masks:
//      maskHoneycomb, maskHexCircles, maskBars, maskOffsetBars
//
//------------------------------------------------------------------
// Shapes should be defined to fit into a 1x1 box (+/-0.5 in X and Y) - they will
// be scaled as needed.
// defined as a vector of [x,y] vertices pairs.(min 3 vertices)
// for example a triangle could be [yappPolygonDef,[[-0.5,-0.5],[0,0.5],[0.5,-0.5]]];
// To see how to add your own shapes and mask see the YAPPgenerator program
//------------------------------------------------------------------


// Show sample of a Mask
//SampleMask(maskHoneycomb);

//===================================================================
// *** PCB Supports ***
// Pin and Socket standoffs
//-------------------------------------------------------------------
//  Default origin =  yappCoordPCB : pcb[0,0,0]
//
//  Parameters:
//   Required:
//    p(0) = posx
//    p(1) = posy
//   Optional:
//    p(2) = Height to bottom of PCB : Default = standoffHeight
//    p(3) = PCB Gap : Default = -1 : Default for yappCoordPCB=pcbThickness, yappCoordBox=0
//    p(4) = standoffDiameter    Default = standoffDiameter;
//    p(5) = standoffPinDiameter Default = standoffPinDiameter;
//    p(6) = standoffHoleSlack   Default = standoffHoleSlack;
//    p(7) = filletRadius (0 = auto size)
//    p(8) = Pin Length : Default = 0 -> PCB Gap + standoff_PinDiameter
//             Indicated length of pin without the half sphere tip.
//             Example : pcbThickness() only leaves the half sphere tip above the PCB
//    n(a) = { <yappBoth> | yappLidOnly | yappBaseOnly }
//    n(b) = { <yappPin>, yappHole, yappTopPin }
//             yappPin = Pin on Base and Hole on Lid
//             yappHole = Hole on Both
//             yappTopPin = Hole on Base and Pin on Lid
//    n(c) = { yappAllCorners, yappFrontLeft | <yappBackLeft> | yappFrontRight | yappBackRight }
//    n(d) = { <yappCoordPCB> | yappCoordBox | yappCoordBoxInside }
//    n(e) = { yappNoFillet } : Removes the internal and external fillets and the Rounded tip on the pins
//    n(f) = [yappPCBName, "XXX"] : Specify a PCB. Defaults to [yappPCBName, "Main"]
//-------------------------------------------------------------------
pcbStands =
[
];


//===================================================================
//  *** Connectors ***
//  Standoffs with hole through base and socket in lid for screw type connections.
//-------------------------------------------------------------------
//  Default origin = yappCoordBox: box[0,0,0]
//
//  Parameters:
//   Required:
//    p(0) = posx
//    p(1) = posy
//    p(2) = pcbStandHeight
//    p(3) = screwDiameter
//    p(4) = screwHeadDiameter (don't forget to add extra for the fillet)
//    p(5) = insertDiameter
//    p(6) = outsideDiameter
//   Optional:
//    p(7) = PCB Gap : Default = -1 : Default for yappCoordPCB=pcbThickness, yappCoordBox=0
//    p(8) = filletRadius : Default = 0/Auto(0 = auto size)
//    n(a) = { <yappAllCorners>, yappFrontLeft | yappFrontRight | yappBackLeft | yappBackRight }
//    n(b) = { <yappCoordBox> | yappCoordPCB |  yappCoordBoxInside }
//    n(c) = { yappNoFillet }
//    n(d) = { yappCountersink }
//    n(e) = [yappPCBName, "XXX"] : Specify a PCB. Defaults to [yappPCBName, "Main"]
//    n(f) = { yappThroughLid = changes the screwhole to the lid and the socket to the base}
//-------------------------------------------------------------------
connectors   =
[
  [
    mm(7), // posx
    mm(7), // posy
    0, // pcbStandHeight
    m3_clearance, // screwDiameter
    m3_flat_head_dia * 1.1, // screwHeadDiameter
    m3_threaded_insert, // insertDiameter
    m3_threaded_insert * 2, // outsideDiameter
    yappAllCorners,
    yappThroughLid, // changes the screwhole to the lid and the socket to the base
    yappNoFillet, // @TODO as of YAPP 3.2.0, fillets are broken (raised above surface) when yappThroughLid is used. They're also omitted on the base in this instance.
  ]
];


//===================================================================
//  *** Cutouts ***
//    There are 6 cutouts one for each surface:
//      cutoutsBase (Bottom), cutoutsLid (Top), cutoutsFront, cutoutsBack, cutoutsLeft, cutoutsRight
//-------------------------------------------------------------------
//  Default origin = yappCoordBox: box[0,0,0]
//
//                        Required                Not Used        Note
//----------------------+-----------------------+---------------+------------------------------------
//  yappRectangle       | width, length         | radius        |
//  yappCircle          | radius                | width, length |
//  yappRoundedRect     | width, length, radius |               |
//  yappCircleWithFlats | width, radius         | length        | length=distance between flats
//  yappCircleWithKey   | width, length, radius |               | width = key width length=key depth
//  yappPolygon         | width, length         | radius        | yappPolygonDef object must be
//                      |                       |               | provided
//  yappRing            | width, length, radius |               | radius = outer radius,
//                      |                       |               | length = inner radius
//                      |                       |               | width = connection between rings
//                      |                       |               |   0 = No connectors
//                      |                       |               |   positive = 2 connectors
//                      |                       |               |   negative = 4 connectors
//----------------------+-----------------------+---------------+------------------------------------
//
//  Parameters:
//   Required:
//    p(0) = from Back
//    p(1) = from Left
//    p(2) = width
//    p(3) = length
//    p(4) = radius
//    p(5) = shape : { yappRectangle | yappCircle | yappPolygon | yappRoundedRect
//                     | yappCircleWithFlats | yappCircleWithKey }
//  Optional:
//    p(6) = depth : Default = 0/Auto : 0 = Auto (plane thickness)
//    p(7) = angle : Default = 0
//    n(a) = { yappPolygonDef } : Required if shape = yappPolygon specified -
//    n(b) = { yappMaskDef } : If a yappMaskDef object is added it will be used as a mask
//                             for the cutout.
//    n(c) = { [yappMaskDef, hOffset, vOffset, rotation] } : If a list for a mask is added
//                              it will be used as a mask for the cutout. With the Rotation
//                              and offsets applied. This can be used to fine tune the mask
//                              placement within the opening.
//    n(d) = { <yappCoordPCB> | yappCoordBox | yappCoordBoxInside }
//    n(e) = { <yappOrigin>, yappCenter }
//    n(f) = { <yappGlobalOrigin>, yappAltOrigin } // Only affects Top(lid), Back and Right Faces
//    n(g) = [yappPCBName, "XXX"] : Specify a PCB. Defaults to [yappPCBName, "Main"]
//    n(h) = { yappFromInside } Make the cut from the inside towards the outside
//-------------------------------------------------------------------
cutoutsBase =
[
];

cutoutsLid  =
[
];

cutoutsFront =
[
];


cutoutsBack =
[
];

cutoutsLeft =
[
];

cutoutsRight =
[
];



//===================================================================
//  *** Snap Joins ***
//-------------------------------------------------------------------
//  Default origin = yappCoordBox: box[0,0,0]
//
//  Parameters:
//   Required:
//    p(0) = posx | posy
//    p(1) = width
//    p(2) = { yappLeft | yappRight | yappFront | yappBack } : one or more
//   Optional:
//    n(a) = { <yappOrigin>, yappCenter }
//    n(b) = { yappSymmetric }
//    n(c) = { yappRectangle } == Make a diamond shape snap
//-------------------------------------------------------------------
snapJoins   =
[
];

//===================================================================
//  *** Box Mounts ***
//  Mounting tabs on the outside of the box
//-------------------------------------------------------------------
//  Default origin = yappCoordBox: box[0,0,0]
//
//  Parameters:
//   Required:
//    p(0) = pos : position along the wall : [pos,offset] : vector for position and offset X.
//                    Position is to center of mounting screw in leftmost position in slot
//    p(1) = screwDiameter
//    p(2) = width of opening in addition to screw diameter
//                    (0=Circular hole screwWidth = hole twice as wide as it is tall)
//    p(3) = height
//    n(a) = { yappLeft | yappRight | yappFront | yappBack } : one or more
//   Optional:
//    p(4) = filletRadius : Default = 0/Auto(0 = auto size)
//    n(b) = { yappNoFillet }
//    n(c) = { <yappBase>, yappLid }
//    n(d) = { yappCenter } : shifts Position to be in the center of the opening instead of
//                            the left of the opening
//    n(e) = { <yappGlobalOrigin>, yappAltOrigin } : Only affects Back and Right Faces
//-------------------------------------------------------------------
boxMounts =
[
];

//===================================================================
//  *** Light Tubes ***
//-------------------------------------------------------------------
//  Default origin = yappCoordPCB: PCB[0,0,0]
//
//  Parameters:
//   Required:
//    p(0) = posx
//    p(1) = posy
//    p(2) = tubeLength
//    p(3) = tubeWidth
//    p(4) = tubeWall
//    p(5) = gapAbovePcb
//    p(6) = { yappCircle | yappRectangle } : tubeType
//   Optional:
//    p(7) = lensThickness (how much to leave on the top of the lid for the
//           light to shine through 0 for open hole : Default = 0/Open
//    p(8) = Height to top of PCB : Default = standoffHeight+pcbThickness
//    p(9) = filletRadius : Default = 0/Auto
//    n(a) = { <yappCoordPCB> | yappCoordBox | yappCoordBoxInside }
//    n(b) = { <yappGlobalOrigin>, yappAltOrigin }
//    n(c) = { yappNoFillet }
//    n(d) = [yappPCBName, "XXX"] : Specify a PCB. Defaults to [yappPCBName, "Main"]
//-------------------------------------------------------------------
lightTubes =
[
];

//===================================================================
//  *** Push Buttons ***
//-------------------------------------------------------------------
//  Default origin = yappCoordPCB: PCB[0,0,0]
//
//  Parameters:
//   Required:
//    p(0) = posx
//    p(1) = posy
//    p(2) = capLength
//    p(3) = capWidth
//    p(4) = capRadius
//    p(5) = capAboveLid
//    p(6) = switchHeight
//    p(7) = switchTravel
//    p(8) = poleDiameter
//   Optional:
//    p(9) = Height to top of PCB : Default = standoffHeight + pcbThickness
//    p(10) = { yappRectangle | yappCircle | yappPolygon | yappRoundedRect
//                    | yappCircleWithFlats | yappCircleWithKey } : Shape, Default = yappRectangle
//    p(11) = angle : Default = 0
//    p(12) = filletRadius          : Default = 0/Auto
//    p(13) = buttonWall            : Default = 2.0;
//    p(14) = buttonPlateThickness  : Default= 2.5;
//    p(15) = buttonSlack           : Default= 0.25;
//    n(a) = { <yappCoordPCB> | yappCoordBox | yappCoordBoxInside }
//    n(b) = { <yappGlobalOrigin>,  yappAltOrigin }
//    n(c) = { yappNoFillet }
//    n(d) = [yappPCBName, "XXX"] : Specify a PCB. Defaults to [yappPCBName, "Main"]
//-------------------------------------------------------------------
pushButtons =
[
];

//===================================================================
//  *** Labels ***
//-------------------------------------------------------------------
//  Default origin = yappCoordBox: box[0,0,0]
//
//  Parameters:
//   p(0) = posx
//   p(1) = posy/z
//   p(2) = rotation degrees CCW
//   p(3) = depth : positive values go into case (Remove) negative valies are raised (Add)
//   p(4) = { yappLeft | yappRight | yappFront | yappBack | yappLid | yappBaseyappLid } : plane
//   p(5) = font
//   p(6) = size
//   p(7) = "label text"
//  Optional:
//   p(8) = Expand : Default = 0 : mm to expand text by (making it bolder)
//-------------------------------------------------------------------
labelsPlane =
[
];


//===================================================================
//  *** Ridge Extension ***
//    Extension from the lid into the case for adding split opening at various heights
//-------------------------------------------------------------------
//  Default origin = yappCoordBox: box[0,0,0]
//
//  Parameters:
//   Required:
//    p(0) = pos
//    p(1) = width
//    p(2) = height : Where to relocate the seam : yappCoordPCB = Above (positive) the PCB
//                                                yappCoordBox = Above (positive) the bottom of the shell (outside)
//   Optional:
//    n(a) = { <yappOrigin>, yappCenter }
//    n(b) = { <yappCoordPCB> | yappCoordBox | yappCoordBoxInside }
//    n(c) = { yappAltOrigin, <yappGlobalOrigin> } // Only affects Top(lid), Back and Right Faces
//    n(d) = [yappPCBName, "XXX"] : Specify a PCB. Defaults to [yappPCBName, "Main"]
//
// Note: Snaps should not be placed on ridge extensions as they remove the ridge to place them.
//-------------------------------------------------------------------
ridgeExtLeft =
[
];

ridgeExtRight =
[
];

ridgeExtFront =
[
];

ridgeExtBack =
[
];


//===================================================================
//  *** Display Mounts ***
//    add a cutout to the lid with mounting posts for a display
//-------------------------------------------------------------------
//  Default origin = yappCoordBox: box[0,0,0]
//
//  Parameters:
//   Required:
//    p(0) = posx
//    p(1) = posy
//    p[2] : displayWidth = overall Width of the display module
//    p[3] : displayHeight = overall Height of the display module
//    p[4] : pinInsetH = Horizontal inset of the mounting hole
//    p[5] : pinInsetV = Vertical inset of the mounting hole
//    p[6] : pinDiameter,
//    p[7] : postOverhang  = Extra distance on outside of pins for the display to sit on - pin Diameter is a good value
//    p[8] : walltoPCBGap = Distance from the display PCB to the surface of the screen
//    p[9] : pcbThickness  = Thickness of the display module PCB
//    p[10] : windowWidth = opening width for the screen
//    p[11] : windowHeight = Opening height for the screen
//    p[12] : windowOffsetH = Horizontal offset from the center for the opening
//    p[13] : windowOffsetV = Vertical offset from the center for the opening
//    p[14] : bevel = Apply a 45degree bevel to the opening
// Optionl:
//    p[15] : rotation
//    p[16] : snapDiameter : default = pinDiameter*2
//    p[17] : lidThickness : default = lidPlaneThickness
//    n(a) = { <yappOrigin>, yappCenter }
//    n(b) = { <yappCoordBox> | yappCoordPCB | yappCoordBoxInside }
//    n(c) = { <yappGlobalOrigin>, yappAltOrigin } // Only affects Top(lid), Back and Right Faces
//    n(d) = [yappPCBName, "XXX"] : Specify a PCB. Defaults to [yappPCBName, "Main"]
//-------------------------------------------------------------------
displayMounts =
[
];

// **********************************************************
// **********************************************************
// **********************************************************
// *************** END OF TEMPLATE SECTION ******************
// **********************************************************
// **********************************************************
// **********************************************************

//---- This is where the magic happens ----

YAPPgenerate();
