import cv2
import numpy as np

def stackImages(imgArray, scale, labels=[]):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    
    if rowsAvailable:
        for x in range(0, rows):
            for y in range(0, cols):
                imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                if len(imgArray[x][y].shape) == 2: 
                    imgArray[x][y] = cv2.cvtColor(imgArray[x][y], cv2.COLOR_GRAY2BGR)
        
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank] * rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
            if len(imgArray[x].shape) == 2: 
                imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        ver = np.hstack(imgArray)

    if len(labels) != 0:
        eachImgWidth = int(ver.shape[1] / cols)
        eachImgHeight = int(ver.shape[0] / rows)
        for d in range(0, rows):
            for c in range(0, cols):
                cv2.rectangle(ver, (c * eachImgWidth, eachImgHeight * d), 
                              (c * eachImgWidth + len(labels[d][c]) * 13 + 27, 30 + eachImgHeight * d), 
                              (255, 255, 255), cv2.FILLED)
                cv2.putText(ver, labels[d][c], (eachImgWidth * c + 10, eachImgHeight * d + 20), 
                            cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 0, 255), 2)
    return ver

def reccounter(contours):
    rectCon = []
    for i in contours:
        area = cv2.contourArea(i)
        #print(area)
        # Filter out small noise
        if area > 50:
            peri = cv2.arcLength(i, True)
            approx = cv2.approxPolyDP(i, 0.05 * peri, True)
        #    print("cornerpoints",len(approx))
            # Only add if it has 4 corners (a rectangle)
            if len(approx) == 4:
                rectCon.append(i)
               # print(rectCon)
    # # Sort by area so the biggest rectangle (the sheet) is first
    rectCon = sorted(rectCon, key=cv2.contourArea, reverse=True)
    return rectCon

def getCornerPoints(cont):
       peri = cv2.arcLength(cont, True)
       approx = cv2.approxPolyDP(cont, 0.05 * peri, True)
    
       return approx

def reorder(myPoints):
     myPoints = myPoints.reshape((4, 2))
     myPointsNew = np.zeros((4, 1, 2), np.int32)
     add = myPoints.sum(1)
     #print(myPoints)
     #print(add)
#     # [top-left, top-right, bottom-left, bottom-right]
     myPointsNew[0] = myPoints[np.argmin(add)] #(0,0)
     myPointsNew[3] = myPoints[np.argmax(add)] #(w,h)
     diff = np.diff(myPoints, axis=1)
     myPointsNew[1] = myPoints[np.argmin(diff)] #(0,w)
     myPointsNew[2] = myPoints[np.argmax(diff)] #(h,0)
     #print(diff)
     return myPointsNew

def splitBoxes(img):
    rows = np.vsplit(img, 30) # Split into 30 questions
    boxes = []
    for r in rows:
        cols = np.hsplit(r, 4) # Split each row into 4 choices (A, B, C, D)
        for box in cols:
            boxes.append(box)
    return boxes

def showAnswers(img, myIndex, grading, ans, questions, choices):
    h = img.shape[0]
    w = img.shape[1]
    
    # --- IMPORTANT: These decimals MUST match the crop from OMR_Main.py! ---
    # Check your OMR_Main.py file (around line 80-83) and make sure 
    # these 4 numbers match EXACTLY what you typed there.
    start_y = int(h * 0.035)  # Shaves off the top 5% (Top border)
    end_y = int(h * 0.985)    # Shaves off the bottom 2% (Bottom border)
    start_x = int(w * 0.22)  # Shaves off the left 24% (Numbers 1-30)
    end_x = int(w * 0.94)    # Shaves off the right 10% (Right margin)

    
    # Calculate the size of the *actual* bubble grid
    crop_w = end_x - start_x
    crop_h = end_y - start_y
    
    secW = int(crop_w / choices)
    secH = int(crop_h / questions)
    
    for x in range(0, questions):
        myAns = myIndex[x]
        
        # Offset the drawing coordinates by adding start_x and start_y!
        cX = start_x + (myAns * secW) + secW // 2
        cY = start_y + (x * secH) + secH // 2
        
        if grading[x] == 1:
            mycolor = (0, 255, 0) # Green for Correct
        else:
            mycolor = (0, 0, 255) # Red for Incorrect
            
            # Draw the correct answer so you know what you missed
            correctAns = ans[x]
            corX = start_x + (correctAns * secW) + secW // 2
            corY = start_y + (x * secH) + secH // 2
            cv2.circle(img, (corX, corY), 30, (0, 255, 0), cv2.FILLED)
            
        # Draw the user's selected answer
        cv2.circle(img, (cX, cY), 30, mycolor, cv2.FILLED)
        
    return img