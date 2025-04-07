import numpy as np
import sys
import cv2
import re
from os import listdir, mkdir, path

# create diff from first image of series to all consecuting
def diffImg(images):
    d = np.zeros(images[0].shape, np.uint8)
    for i in range(1,  len(images)):
        d = cv2.bitwise_or(cv2.absdiff(images[0],images[i]),d)
    return d

def process_images(pathToProcess):
    filesToProcess = []
    for file in listdir(pathToProcess):
        if file.endswith(".bmp"):
            filesToProcess.append(file)

    ## Load Images
    # all images to process
    imagesBW = []
    originals = []
    allive = 0

    # regexpattern to find *.bmp files
    pattern = re.compile('.*.bmp', re.IGNORECASE)
    for fileName in filesToProcess:
        if(pattern.match(fileName)):
            originals.append(cv2.imread(pathToProcess + '/' + fileName))

            image = cv2.imread(pathToProcess + '/' + fileName,0)
            image = cv2.fastNlMeansDenoising(image,templateWindowSize=7,searchWindowSize=21) #7 and 21
            imagesBW.append(image)# load image as grayscale
        else:
            filesToProcess.remove(fileName)

    ##  Show the Differential Image
    differentialImage = diffImg(imagesBW)
    #plt.imshow(differentialImage,cmap="gray")
    #plt.show()

    ##  Postprocessing
    #   threshold of mask
    #differentialImage = cv2.GaussianBlur(differentialImage,(1,1),5)

    ret,mask = cv2.threshold(differentialImage, 25, 255, cv2.THRESH_BINARY)

    #mask = cv2.adaptiveThreshold(differentialImage,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)

    # ret,mask = cv2.threshold(blur,30,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    activity = cv2.bitwise_or(originals[0], originals[0], mask=cv2.bitwise_not(mask))
    background = np.full(originals[0].shape, (57,255,20), dtype=np.uint8)
    background = cv2.bitwise_or(background, background, mask=mask)
    activity = cv2.bitwise_or(activity, background);

    #   increase the size of the spots
    kernel = np.ones((3,3),np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=5) # increase the size of the found spots
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) # close holes

    #   Find contours
    contours, hier = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        (x, y), radius = cv2.minEnclosingCircle(contour) # find circle around the movement
        center = (int(x), int(y))
        tmpMask = np.zeros((mask.shape[0],mask.shape[1]), np.uint8)

        ##allignment arround movement
        for i in range(0,len(originals)):
            cv2.circle(originals[i], center, 20, (255, 0, 0), 1)

        # #alligment arround varroa
        # # nicer but slower and more error prone
        # cv2.circle(tmpMask, center, 20, 255, -1) # add cirle to mask
        # imageBWInverted = cv2.bitwise_not(imagesBW[0])
        # varroa = cv2.bitwise_and(imageBWInverted,imageBWInverted,mask=tmpMask)
        # _, varroaTreshold = cv2.threshold(varroa, 100, 255, cv2.THRESH_BINARY)
        # varroaMask = cv2.dilate(varroaTreshold, kernel, iterations=5) # increase the size of the found spots
        # varroaMask = cv2.morphologyEx(varroaMask, cv2.MORPH_CLOSE, kernel) # close holes
        # _, varroaContours, _ = cv2.findContours(varroaMask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # if len(varroaContours) > 1:
        #     print "too many varroa contours detected on one spot. but should not be a problem"
        # if len(varroaContours) != 1:
        #     print "no varroa contour found on one spot"
        # else:
        #     (x, y), radius = cv2.minEnclosingCircle(varroaContours[0])
        #     center = (int(x), int(y))
        #     for i in range(0,len(originals)):
        #         cv2.circle(originals[i], center, 20, (255, 0, 0), 3)

    allive = str(len(contours))
    print("Found " + allive + " varroa alive.")

    if not path.exists(pathToProcess + '/results/'):
        mkdir(pathToProcess + '/results/')
    for i in range(0, len(originals)):
        cv2.imwrite(pathToProcess + '/results/marked_' + filesToProcess[i].replace('bmp', 'png'), originals[i])
    cv2.imwrite(pathToProcess + '/results/activity.png', activity)


if __name__ == '__main__':
    # The path where one sample (burst of images) is stored
    pathToProcess = str(sys.argv[1])

    process_images(pathToProcess)

