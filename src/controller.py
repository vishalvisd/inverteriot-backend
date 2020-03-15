from flask import *
from flask_cors import CORS
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory, PNReconnectionPolicy
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
import time

pnconfig = PNConfiguration()

pnconfig.subscribe_key = 'sub-c-2ee8f996-6133-11ea-aaa3-eab2515ceb0d'
pnconfig.publish_key = 'pub-c-150da624-63d5-4b29-812c-dde769508367'
pnconfig.reconnect_policy = PNReconnectionPolicy.LINEAR
pnconfig.uuid = "my_custom_uuid1"

pubnub = PubNub(pnconfig)
app = Flask(__name__)
CORS(app)

serailcount = -1
ack = None

def getSerial():
    global serailcount
    if serailcount == 9:
        serailcount = -1
    serailcount = serailcount + 1
    return serailcount

def my_publish_callback(envelope, status):
    if not status.is_error():
        pass
    else:
        pass

class MySubscribeCallback(SubscribeCallback):
    def presence(self, pubnub, presence):
        pass

    def status(self, pubnub, status):
        if status.category == PNStatusCategory.PNConnectedCategory:
            print("subscribed")
            global ack
            ack = "subscribed"

    def message(self, pubnub, message):
        global ack
        print(f'messag:: {message.message}')
        if (not isinstance(message.message, dict)):
            ack = message.message


@app.route('/setinstruction')
def setCurrentInstruction():
    result = {
        "subscribing": {
            'error': None,
            'errorMessage': None,
        },
        "edgeDeviceApplying": {
            'error': None,
            'errorMessage': None,
            'edgeDeviceApplySuccess': False
        },
        'ack': None
    }

    instruction = request.args.get('ins', type=str)

    timeout = time.time() + 15 # 15 seconds from now
    global ack
    ack = None
    pubnub.subscribe().channels('visdInverterOperator01In').execute()
    while True:
        if ack == 'subscribed':
            print("subscribed understood")
            break
        if time.time() > timeout:
            result["subscribing"]["error"] = True
            result["subscribing"]["errorMessage"] = "timeout"
            break
    if ack is not 'subscribed':
        result['ack'] = ack
        ack = None
        return jsonify(result)

    currentSerial = getSerial()
    pubnub.publish().channel("visdInverterOperator01In").message({
        "ins": instruction,
        "serial": currentSerial
    }).pn_async(my_publish_callback)

    ack = None
    timeout = time.time() + 15 # 15 seconds from now
    while True:
        if ack is not None and int(ack) == currentSerial:
            result['edgeDeviceApplying']['error'] = False
            result['edgeDeviceApplying']['errorMessage'] = None
            result['edgeDeviceApplying']['edgeDeviceApplySuccess'] = True
            result['ack'] = ack
            ack = None
            break
        if time.time() > timeout:
            result['edgeDeviceApplying']['error'] = True
            result['edgeDeviceApplying']['errorMessage'] = 'timeout'
            result['edgeDeviceApplying']['edgeDeviceApplySuccess'] = False
            result['ack'] = ack
            break
    ack = None

    pubnub.unsubscribe().channels('visdInverterOperator01In').execute()

    return jsonify(result)

pubnub.add_listener(MySubscribeCallback())
if __name__ == '__main__':
    app.run(host='0.0.0.0')