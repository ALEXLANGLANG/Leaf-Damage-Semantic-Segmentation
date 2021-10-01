# Leaf Damage Semantic Segmentation

## LeavesImageEditor
This editor helps us to decrease the class imbalance ratio (negative pixels/positive pixels) to 205 from 415. It only takes us 4~6s to process one image which is acceptable in indutries where people spent a few minitues on annotation. 
### Steps
1. ```python 
   pip install -r requirements.txt
2. Set up configuration file: config_image_editor.yml. Put your data directory here
3. In PyCharm,  run run.py
4. Process the image
    1) Select a single image or select all images in dataset
    1) Crop the image
    2) Remove the area with noise
    3) Adjust the Ostu's threshold and remove small holes or objects to clear the background
    4) Save and next
   
Select images|
:-------------------------:|
![sample_original](https://user-images.githubusercontent.com/49976598/135553660-943cdf2e-f4bd-4e17-8a59-76a46d36d355.jpg)

Use adjust to extract the foreground|
:-------------------------:|
![sample_adjust](https://user-images.githubusercontent.com/49976598/135553659-6cede6ff-ccd1-4bc2-9427-ed10c881a0db.jpg)

Save the clean data and go next|
:-------------------------:|
![sample_clean](https://user-images.githubusercontent.com/49976598/135553658-4ff8255f-c3dd-40b0-a7e0-1880dd94062a.jpg)

## Copy/paste data augmentation 
This section will be published later


## Performance
This section will be published later
