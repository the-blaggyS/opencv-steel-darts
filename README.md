# opencv-steel-darts
Automatic scoring system for steel darts using OpenCV and one or two webcams.

Main entry point is *DartsScorer.py*.

Watch a demo of the original setup here: https://www.youtube.com/playlist?list=PLqymqC7nbI7an1dZW1kxbPPd-v0t5l6lF

Detected darts with score mapping and a Test-GUI to play simple 501:

![Detection](Bilder/Darts_Detection_NEW.png) ![GUI](Bilder/GAME_Recognition.jpeg)

I would like to point to this project as well. Two camera system but placed at the side of the board using triangulation:
https://github.com/vassdoki/opencv-darts

We have created a Facebook Group, where we discuss our current progress and try to help each other:
https://www.facebook.com/groups/281778298914107/

### ToDo: 
* improve calibration routine
* develop dedicated frontend application
* develop dart heatmap and implement better analytics

## Calibration

The transformation works like that (reading from right to left):

			M=T2⋅R2⋅D⋅R1⋅T1
			
1. moves the ellipse-center to the origin
2. rotates the ellipse clockwise about the origin by angle θ, so that the major axis lines up with the x-axis.
3. scales the y-axis up so that it's as fat in y as in x.
4. rotates counterclockwise by θ.
5. translates the ellipse-center back to where it used to be.

(https://math.stackexchange.com/questions/619037/circle-affine-transformation)

**The same procedure applies for the left camera!**

### Calibrated board

![ellipse-circle](Bilder/Dartboard_Calibration.jpg)

## Darts Detection

*insert text here (short version: To detect the dart I use the diff between images and then the good_features_to_track method from opencv with some pre-and post-processing methods + score merging of both cameras).

## Lighting and Camera placement

![ellipse-circle](Bilder/Lighting.jpg)

## License
GNU General Public License v3.0
