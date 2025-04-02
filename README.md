# I HAVE BROKE SOMETHING AND IT IS NO LONGER CANCELING THE PRINT. DO NOT USE CURRENTLY. 

# Qidi-Plus-4-Bed-plate-object-detection
This is a mod for the Qidi plus 4 to detect if there is a current object on the build plate. This is to prevent starting prints with a print on the bed or without the build plate installed.
Let's be clear this is a mod, I am not responsible for your printer or any damages that could occur. I have done some testing with it but make no gaurrentees. 
Make sure you create a back up of klipper + Config files incase you want to revert or mess up along the way. 

# Things to know
Anytime after a manual home the printer will need to be put back into position to read the empty bed. X5 Y300 Z140

Anytime you change build plates or damage one enought that it appears as a defect you will need to retake the empty bed photos. See step 6.

If you have any other changes such as front covers/belts accessories in camera view you will need to take new photos. 

If you have a carto/beacon and your wires are all floppy this will probably cause you issues.

Theres probably more but I've only minimally tested this.

Obviously if the camera cant see it then it can't be detected so don't go leaving stuff in the front right corner where the camera can't see. 


# Temporary problems
~~The End print macro sends it to the bottom of the printer everytime. I believe this is being caused by the end gcode in orca slicer. Will look into that soon and update instructions.~~ FIXED

Will add fixable problems here. 

# Step one - Installing Open CV to the klippy python enviorment
First we need to SSH into the printer. You can do this however you feel like. See https://github.com/qidi-community/Plus4-Wiki/blob/main/content/ssh-access/README.md

Now that we have ssh access we need to get into the klippy python enviorment. 
```
source ~/klippy-env/bin/activate
```
Now that we are in the klippy python enviorment we can install open cv

```
pip install opencv-python
```

Once open-cv is installed we can exit the python Enviorment

```
deactivate
```
# Step Two - Adding the bed detection python script to klipper
Now we need to navigate to the extras directory. 
```
cd ~/klipper/klippy/extras
```
Next we need to create the python file 
```
nano cv2_bed_object_detect.py
```
Now that you have cv2bedobjectdetect.py open in nano copy the contents of the file cv2bedobjectdetect.py from this github directory (simple copy and paste into shell terminal should work) and ctrl+S to save and ctrl+x to exit nano. 

# Step Three - Adding the CFG file. 
First we will navigate to the klipper config directory
```
cd ~/klipper_config
```
Next we will create the config file
```
nano cv2_bed_object_detect.cfg
```
Now that nano is open all we need to do is add
```
[cv2_bed_object_detect]
```
and press ctrl+s to save and ctrl+x to exit nano

# Step Four - making the directory for the bed photos
first we move to the correct directory
```
cd ~
```
then we make the new folder
```
mkdir cv2bedobjectdetect
```

# Step Four - editing printer.cfg
At this point I would move over to fluidd and being doing the work through the web interface. 
in your printer.cfg file under the current includes (right above the mcu section) add
```
[include cv2_bed_object_detect.cfg]
```
Save

# Step Five - Editing the macros. 

So currently we only have 3 macros to edit. There might be more in the fucture but this is the basics. 
Once again I would use Fluidd to edit these commands. They are located in gcode_macro.cfg

Print_start

This needs to be added at the very top of your print_start routine. These should be the first thing that happens at the start of a print. 
```
    CAPTURE_IMAGE_CURRENT_BED
    M400
    CHECK_OBJECT_ON_BED
    M400
```

End_Print Macro
This should be put in after first M400 located inside of the end print macro.
```
    {% if (printer.gcode_move.position.z) <= 137 %}
    G1 Z140 F600  
    {% else %}
    G1 Z250 F600
    {% endif %}
    G1 X5 Y300 F7800
```

Cancel_Print Macro
This should be put in at the top of the CANCEL_PRINT macro
```
    {% if (printer.gcode_move.position.z) <= 137 %}
    G1 Z140 F600  
    {% else %}
    G1 Z250 F600
    {% endif %}
    G1 X5 Y300 F7800
```
# Step Six - Capturing empty bed photos.
THIS WILL NEED TO BE DONE EVERY TIME YOU CHANGE TO A NEW BUILD PLATE OR CAUSE DAMAGE TO YOUR CURRRENT ONE!!!
First Check your printer and make sure there is nothing on the bed ;) Currently this has to be done with your eyes. 
In your fluidd console
Home Your printer. 
```
g28
```
Now lets move to the correct position for capturing empty bed images 
first our x and y
```
g1 x5 y300 f7800
```
Now our z
```
g1 z140 f600
```
Now lets capture our first empty bed photo. 
```
CAPTURE_IMAGE_EMPTY_BED_140
```
You should see the following message in your console
```
// Empty bed image captured and saved to /home/mks/cv2bedobjectdetect/emptybed140.jpg
```
next lext move to captures the second bed image
```
g1 z250 f600
```
Now we take our second empty bed photo
```
CAPTURE_IMAGE_EMPTY_BED_250
```
You should see the following message in your console
```
// Empty bed image captured and saved to /home/mks/cv2bedobjectdetect/emptybed250.jpg
```
# Step Seven - Editing Machine end g-code in slicer.
Since we are handling this in the klipper gcode we can get rid of it setting the XYZ Position after the print is done. 
```
M141 S0
M104 S0
M140 S0
G1 E-3 F1800
```

# Ta-Dah We are done






