#part-handler

import base64


def list_types():
    # return a list of mime-types that are handled by this module
    result = ["application/base64"]
    print("list_types(): {}".format(result))
    return result

def handle_part(data, ctype, filename, payload):
    # data: the cloudinit object
    # ctype: '__begin__', '__end__', or the specific mime-type of the part
    # filename: the filename for the part, or dynamically generated part if
    #           no filename is given attribute is present
    # payload: the content of the part (empty for begin or end)
    if ctype == "__begin__" or ctype == "__end__":
        return

    print("Writing {}...".format(filename))
    with open(filename, 'wb') as f:
        decoded = base64.b64decode(payload)
        f.write(decoded)
