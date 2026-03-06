import cv2
import numpy as np
import utlis
import os

def grade_sheet(image_path, output_path,ans):
    # Standard settings from your OMR_Main
    widthImg = 700
    heightImg = 1650
    questions = 30
    choices = 4
    #ans = [0, 0, 1, 0, 1, 0, 0, 3, 1, 0, 0, 1, 0, 1, 2, 1, 3, 1, 0, 1, 0, 1, 3, 0, 1, 0, 1, 0, 1, 0]

    img = cv2.imread(image_path)
    img = cv2.resize(img, (widthImg, heightImg))
    imgFinal = img.copy()
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
    imgCanny = cv2.Canny(imgBlur, 10, 50)

    # Finding contours
    contours, _ = cv2.findContours(imgCanny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    rectCon = utlis.reccounter(contours)
    
    # Error handling if sheet isn't found
    if len(rectCon) < 2:
        return 0, image_path 

    biggestContour = utlis.reorder(utlis.getCornerPoints(rectCon[0]))
    gradepoints = utlis.reorder(utlis.getCornerPoints(rectCon[1]))

    # Perspective Warp
    pt1 = np.float32(biggestContour)
    pt2 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])
    matrix = cv2.getPerspectiveTransform(pt1, pt2)
    imgWarpColoured = cv2.warpPerspective(img, matrix, (widthImg, heightImg))

    # Grading Warp
    ptG1 = np.float32(gradepoints)
    ptG2 = np.float32([[0, 0], [325, 0], [0, 150], [325, 150]])
    matrixG = cv2.getPerspectiveTransform(ptG1, ptG2)
    imgGradeDisplay = cv2.warpPerspective(img, matrixG, (325, 150))

    # Thresholding
    imgWarpGray = cv2.cvtColor(imgWarpColoured, cv2.COLOR_BGR2GRAY)
    imgThresh = cv2.threshold(imgWarpGray, 170, 255, cv2.THRESH_BINARY_INV)[1]

    # Cropping Logic (Using your exact decimals)
    h, w = imgThresh.shape
    start_y, end_y = int(h * 0.03), int(h * 0.98)
    start_x, end_x = int(w * 0.21), int(w * 0.95)
    imgThresh_Bubbles = imgThresh[start_y:end_y, start_x:end_x]
    imgThresh_Bubbles = cv2.resize(imgThresh_Bubbles, (400, 1500))
    
    boxes = utlis.splitBoxes(imgThresh_Bubbles)
    myPixelval = np.zeros((questions, choices))
    countC, countR = 0, 0

    for image in boxes:
        totalPixels = cv2.countNonZero(image)
        myPixelval[countR][countC] = totalPixels
        countC += 1
        if countC == choices:
            countR += 1
            countC = 0

    myIndex = []
    for x in range(questions):
        arr = myPixelval[x]
        myIndexVal = np.where(arr == np.amax(arr))
        myIndex.append(myIndexVal[0][0])

    grading = [1 if ans[x] == myIndex[x] else 0 for x in range(questions)]
    score = (sum(grading) / questions) * 100

    # Drawing results
    imgRawDrawing = np.zeros_like(imgWarpColoured)
    imgRawDrawing = utlis.showAnswers(imgRawDrawing, myIndex, grading, ans, questions, choices)
    invMatrix = cv2.getPerspectiveTransform(pt2, pt1)
    imgInvWarp = cv2.warpPerspective(imgRawDrawing, invMatrix, (widthImg, heightImg))

    imgRawGrade = np.zeros_like(imgGradeDisplay)
    cv2.putText(imgRawGrade, f"{int(score)}%", (60, 100), cv2.FONT_HERSHEY_COMPLEX, 3, (0, 255, 255), 3)
    invMatrixG = cv2.getPerspectiveTransform(ptG2, ptG1)
    imgInvGradeDisplay = cv2.warpPerspective(imgRawGrade, invMatrixG, (widthImg, heightImg))

    imgFinal = cv2.addWeighted(imgFinal, 1, imgInvWarp, 1, 0)
    imgFinal = cv2.addWeighted(imgFinal, 1, imgInvGradeDisplay, 1, 0)

    # Save the final graded image to the uploads folder
    cv2.imwrite(output_path, imgFinal)

    return int(score), output_path