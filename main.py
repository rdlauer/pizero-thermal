import cv2
import os
import time
import thermal
import keys
import notecard
from edge_impulse_linux.image import ImageImpulseRunner
from notecard import hub, note
from periphery import I2C

# initialize variables for Edge Impulse
runner = None
dir_path = os.path.dirname(os.path.realpath(__file__))
modelfile = os.path.join(dir_path, "modelfile.eim")

# initialize the Blues Wireless Notecard (blues.io)
productUID = keys.PRODUCT_UID
port = I2C("/dev/i2c-1")
nCard = notecard.OpenI2C(port, 0, 0)

# associate Notecard with a project on Notehub.io
hub.set(nCard, product=productUID, mode="periodic", outbound=30, inbound=720)

req = {"req": "hub.sync"}
nCard.Transaction(req)


def main():

    print('MODEL: ' + modelfile)

    with ImageImpulseRunner(modelfile) as runner:
        try:
            model_info = runner.init()
            print('Loaded runner for "' +
                  model_info['project']['owner'] + ' / ' + model_info['project']['name'] + '"')
            labels = model_info['model_parameters']['labels']

            # grab image from thermal camera
            filename = thermal.takePicture()
            img = cv2.imread("images/" + filename)

            if img is None:
                print('Failed to load image')
                exit(1)

            features, cropped = runner.get_features_from_image(img)

            # optional: write debug.jpg
            #cv2.imwrite('debug.jpg', cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR))

            res = runner.classify(features)

            if "classification" in res["result"].keys():
                print('Result (%d ms.) ' % (
                    res['timing']['dsp'] + res['timing']['classification']), end='')
                note_body = {}
                for label in labels:
                    score = res['result']['classification'][label]
                    print('%s: %.2f\t' % (label, score), end='')
                    note_body[label] = round(score, 4)

                print('', flush=True)

                note.add(nCard,
                         file="thermal.qo",
                         body=note_body)

        finally:
            if (runner):
                runner.stop()


while True:
    main()
    time.sleep(60 * 5)
