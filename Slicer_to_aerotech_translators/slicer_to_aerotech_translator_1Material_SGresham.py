''' NOTES
- must use slic3r profile (from Nathan) -- need to add to SharePoint... where the follow are true:
    -  extruding G-code lines are marked by 0.00000 at end of line
    - material is not extruding when feed rate (F#) is at the end of the line


- to create print path from an image do the following:
    1. download high resolution image
    2. upload to solidworks as a .dxf file
    (you can use illustrator see below or use an online converter)

    converting to .dxf
    1. upload image into Adobe Illustrator
    2. with image selected: Object > rasterize > turn on transparency
    3. with image selected: Object > image trace
    4. export as .dxf

'''


## Single material prints
###################### IMPORT / EXPORT FILES ##############################################################################################################
import_gcode_txt = "SGresham_rectangle_knot_micro.txt"             # upload gcode as txt file (i.e., must include .txt)
export_gcode_txt = "SGresham_rectangle_knot_micro_aerotech.txt"    # export gcode as txt file (i.e., must include .txt)

intro_flag = True       # False             # mark True if you want to add an intro; mark False if you don't want to add an intro
ending_flag = True      # False             # mark True if you want to add an ending; mark False if you don't want to add an ending
intro_gcode = "SGresham_aerotech_intro.txt"
ending_gcode = "SGresham_aerotech_end.txt"

######################## DEFINE PARAMETERS ################################################################################################################

Z_var = "C" # format: "axis" ; replaces Z with aerotech axis variable

#### PRESSURE BOXES ####
com = [5]
pressure = [60]

#### Intro / Ending Variables (only used if they are specified in intro gcode using format {variable name} --- (see SPropst_aerotech_intro.txt as example)
feed = 20                  # mm/s           # e.g., G1 F{feed}
ramprate = 900             # mm/s^2         # e.g., RAMP RATE {ramprate}
Z_height = 0.5             # mm             # z_height for the first layer (used to calculate Z_start)
Z_start = -150 + Z_height  # mm             # e.g., G0 {Z_var}{Z_start} ; tells the printer what z position to start at (-150 assumes you are starting from the lowest point on axis)

file_name = ["$hFile"]                      # e.g., DVAR {file_name} : used to open connection between aerotech and pressure boxes

#### DEFINE Pressure Values and Toggle on/off ####
def setpress(pressure):
    # IMPORTS
    from codecs import encode
    from textwrap import wrap

    pressure = str(int(pressure * 10))
    length = len(pressure)
    while length < 4:
        pressure = "0" + pressure
        length = len(pressure)

    commandc = bytes(('08PS  ' + pressure), "utf-8")

    # FIND CHECKSUM
    startc = b'\x05\x02'
    endc = b'\x03'

    hexcommand = encode(commandc, "hex")  # encode should turn this into a hex rather than ascii

    hexcommand = hexcommand.decode("utf-8")  # decode should turn this into a string object rather than a bytes object

    ####format for arduino#####
    format_command = str(hexcommand)
    format_command = '\\x'.join(format_command[i:i + 2] for i in range(0, len(format_command), 2))
    format_command = '\\x'+format_command
    ##########################

    hexcommand = wrap(hexcommand,
                      2)  # wrap should split the string into a horizontal array of strings of 2 characters each

    # GETTING THE 8 BIT 2'S COMPLEMENT
    decimalsum = 0
    for i in hexcommand:  # get the decimal sum of the hex command
        decimalsum = decimalsum + int(i, 16)
    checksum = decimalsum % 256  # get the remainder of the decimal sum
    checksum = bin(checksum)  # turn into binary
    checksum = checksum[2:]  # checksum is a string
    while len(checksum) < 8:  # checksum must represents 8 bits of information
        checksum = "0" + checksum
    invert = ""
    for i in checksum:  # binary sum must be inverted
        if i == '0':
            invert = invert + "1"
        else:
            invert = invert + "0"
    invert = int(invert, 2)  # binary sum turned into decimal form
    invert = invert + 1
    # CHECKSUM HAS BEEN RETRIEVED IN DECIMAL FORM
    checksum = invert
    checksum = hex(checksum)  # checksum is in the format "0x##"
    # CHECKSUM IS NOW IN ASCII FORM, don't be mislead by the hex function
    checksum = checksum[2:]
    checksumarray = []
    for i in checksum:  # must get alphabetical characters in uppercase for ascii to hex conversion
        if i.isalpha():
            i = i.upper()
            checksumarray.append(i)
        else:
            checksumarray.append(i)
    checksum = ""
    for i in checksumarray:
        checksum = checksum + i
    # checksum is a string.
    checksum = bytes(checksum, 'ascii')

    ####format for arduino#####
    hexchecksum = encode(checksum, 'hex')
    hexchecksum = hexchecksum.decode("utf-8")  # decode should turn this into a string object rather than a bytes object
    format_checksum = str(hexchecksum)  # format for arduino
    format_checksum = '\\x'.join(format_checksum[i:i + 2] for i in range(0, len(format_checksum), 2))
    format_checksum = '\\x' + format_checksum

    # SENDING OUT THE COMMAND
    ##format for arduino####
    finalcommand = ('\\x05\\x02') + format_command + format_checksum + str('\\x03')
    finalcommand = finalcommand.strip('\r').strip('\n')
    finalcommand = '"' + finalcommand + '"'
    return finalcommand
def togglepress():
    # IMPORTS
    import serial
    from codecs import encode
    from textwrap import wrap
    toggle = str('"\\x05\\x02\\x30\\x34\\x44\\x49\\x20\\x20\\x43\\x46\\x03"')
    return toggle

setpress_val = str('\n\rFILEWRITE ' + file_name[0] + str(setpress(pressure[0])) + '\r\n')           # set pressure
toggleON_1 = str('\n\rFILEWRITE ' + file_name[0] + str(togglepress()))                              # toggle on/off
toggleOFF_1 = toggleON_1

######################## RUN CODE ###########################################################################################################################

## Opens gcode file, removes comments, changes commands to fit aerotech (e.g. G2 --> CW, Z --> D) turns it into a list
def open_gcode(gcode_txt):
    gcode_list = []
    with open(gcode_txt, "r") as gcode:
        for myline in gcode:  # For each elem in the file,
            if ";" not in myline or "G90" in myline or "G91" in myline: # removes comments
                gcode_list.append(myline.strip('\n').replace('Z', Z_var).replace('G21', '; G21').replace('G2','CW').replace('G3','CCW'))

            # print(myline)
        gcode_list = [x for x in gcode_list if x != ""] # removes spaces
        gcode.close()
        return gcode_list
gcode_list = open_gcode(import_gcode_txt)

## Translate gcode to be used with the aerotech
def parse_gcode(gcode_list):
    def find(s, ch):  # s = string to search, ch = character to find
        # s = a string
        # ch = character to find
        return [i for i, ltr in enumerate(s) if ltr == ch]
    gcode_dict = {}

    for i in range(len(gcode_list)):
        gcode_dict[i] = gcode_list[i].split(" ")
        find_extrusion = find(gcode_dict[i], "2.00000")
        find_comment = find(gcode_dict[i], ";")
        find_CW_moves = find(gcode_dict[i], "CW")
        find_CCW_moves = find(gcode_dict[i], "CCW")

        for j in range(len(gcode_dict[i])):
            find_feed = find(gcode_dict[i][j], "F")  # if feed rate is redefined, material is not extruding
            if find_feed != [] and find_comment != [0]:
                del gcode_dict[i][j]
                gcode_dict[i].append(';not extruding')

        if find_extrusion != []: # if extrusion flag is found: removes flag and adds extruding comment
            del gcode_dict[i][find_extrusion[0]]
            gcode_dict[i].append(';extruding')

        if find_CW_moves != [] or find_CCW_moves != []: # material is extruding during circular moves
            gcode_dict[i].append(';extruding')
    gcode_list = []

    for i in range(len(gcode_dict)):
        combine = ''
        for elem in gcode_dict[i]:
            combine += elem + ' '
        gcode_list.append(combine)
    return gcode_list
gcode_list = parse_gcode(gcode_list)

## Writes aerotech intro to final file (only runs if you flagged it as true)
def intro(intro_gcode, export_gcode_txt, Z_var, ramprate, feed, Z_start):
    with open(intro_gcode, "r") as g:
        with open(export_gcode_txt, 'w') as f:
            for line in g:
                line = line.replace('{file_name}', file_name[0]).replace('{Z_var}', Z_var).replace('{ramprate}', str(ramprate)).replace('{feed}', str(feed)).replace('{Z_start}', str(Z_start))
                line = line.replace('{com}', str(com[0]))
                line = line.replace('{setpress}', str(pressure[0]))
                f.write(line)
        g.close()

    return f
    f.close()
if intro_flag == True:
    intro_export = intro(intro_gcode, export_gcode_txt, Z_var, ramprate, feed, Z_start)

## Writes translated code to final file
def export_gcode(gcode_list, export_gcode_txt, intro_flag):
    if intro_flag == True:
        type_open = "a"
    else:
        type_open = "w"
    with open(export_gcode_txt, type_open) as f:
        # f.write("\n\rFILECLOSE")
        # f.write("\n" + file_name[0] + ' = FILEOPEN "COM' + str(com[0]) + '", 2')
        # f.write('\nCOMMINIT ' + file_name[0] + ', "baud=115200 parity=N data=8 stop=1"')
        # f.write('\nCOMMSETTIMEOUT ' + file_name[0] + ', -1, -1, 1000')
        #
        # f.write('\n' + setpress_val)
        on = False
        not_extruding_count = 0
        for i in range(len(gcode_list)):
            elem = gcode_list[i]
            if "G1 ;not extruding " in elem:
                f.write('')
            elif "G1 0.00000 ;not extruding " in elem:
                f.write('')
            elif ";not extruding " in elem and on == True:
                f.write(toggleOFF_1)
                f.write('\n'+elem)
                on = False
            elif ';extruding ' in elem and on == False:
                f.write(toggleON_1)
                f.write("\nDWELL 0.15")
                f.write('\n'+elem)
                on = True
            else:
                f.write('\n'+elem)

        if on == True:
            f.write(toggleOFF_1)

    return f
    f.close()
final_gcode = export_gcode(gcode_list,export_gcode_txt, intro_flag)

## Writes aerotech ending to final file (only runs if you flagged it as true)
def ending(ending_gcode, export_gcode_txt, Z_var):
    with open(ending_gcode, "r") as g:
        with open(export_gcode_txt, 'a') as f:
            f.write('\n\r')
            for line in g:
                f.write(line.replace('{Z_var}', Z_var))
        g.close()

    return f
    f.close()
if ending_flag == True:
    ending_export = ending(ending_gcode, export_gcode_txt, Z_var)