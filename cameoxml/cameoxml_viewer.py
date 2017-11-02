###########################################################################
# Copyright 2016 Raytheon BBN Technologies Corp. All Rights Reserved.     #
#                                                                         #
###########################################################################


import sys, os, codecs, sqlite3, argparse, re
import cameoxml
from xml.etree import ElementTree as ET

# Get dictionary of Event Codes : Descriptions
def get_event_code_descriptions(event_descriptions_file):
    event_code_descriptions = {}

    f = open(event_descriptions_file, 'r')

    for line in f:
        pieces = line.split(':')
        code = pieces[0].strip()
        description = pieces[1].strip()
        if description.endswith(" below"):
            description = description[:-6]
        event_code_descriptions[code] = description

    f.close()

    return event_code_descriptions

def write_main_HTML_file(output_dir, cameoxml_filename):
    output_file = os.path.join(output_dir, cameoxml_filename + ".html")
    f_o = codecs.open(output_file, 'w', 'utf-8')
    f_o.write('''
        <!DOCTYPE html>
        <html>
        <meta charset="UTF-8">
        <style>
        iframe {
                overflow: hidden;
        }
        #events {
                 position: absolute;
                 left: 50%;
         width: 49%;
    }
    #text {
        position: absolute;
        width: 49%;
        left: 0px;
    }
    </style> 
    <head>
    </head>
    <body>
        <iframe id="text" name="text" width="50%" height="100%" src="parts/''' + cameoxml_filename + '''_text.html"></iframe>
        <iframe id="events" name="events" width="50%" height="100%" src="parts/''' + cameoxml_filename + '''_events.html"></iframe>
    </body>
    </html>
    ''')
    f_o.close()

def write_text_HTML_file(output_dir, cameoxml_filename, text_body):

    # Make sure subdirectory exists
    path = os.path.join(output_dir, "parts")
    try: 
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise

    # Write beginning of HTML file
    output_file = os.path.join(path, cameoxml_filename + "_text.html")
    f_o = codecs.open(output_file, 'w', 'utf-8')
    f_o.write("""
    <!DOCTYPE html>
    <html>
    <meta charset="UTF-8"> 
    <style>
    a {text-decoration: none}
    a:link, a:visited {color: blue}
    body {padding-bottom: 100%}
    .cCC00CClink {color: CC00CC}
    .cbluelink {color: blue}
    .c8b0000link {color: 8b0000}
    .c33CCFFlink {color: 33CCFF}
    .credlink {color: red}
    .corangelink {color: orange}
    .c006400link {color: 006400}
    .cgreenlink {color: green}
    .cblacklink {color: black}
    </style>
    <head>
    <title>""" + cameoxml_filename + """</title>
    </head>
    <body>
    """ + text_body + """
    <script>
    var elements = document.getElementsByTagName('a');
    for(var i = 0, len = elements.length; i < len; i++) {
        elements[i].addEventListener("click", function(){
        }); 
    }
    </script>
    </body>
    </html>
    """)
    f_o.close()


def write_events_HTML_file(output_dir, cameoxml_filename, events_body):

    # Make sure subdirectory exists
    path = os.path.join(output_dir, "parts")
    try: 
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise

    # Write beginning of HTML file
    output_file = os.path.join(path, cameoxml_filename + "_events.html")
    f_o = codecs.open(output_file, 'w', 'utf-8')
    f_o.write("""
    <!DOCTYPE html>
    <html>
    <meta charset="UTF-8"> 
    <style>
    a {text-decoration: none}
    a:link, a:visited {color: blue}
    body {padding-bottom: 100%}
    .cCC00CClink {color: CC00CC}
    .cbluelink {color: blue}
    .c8b0000link {color: 8b0000}
    .c33CCFFlink {color: 33CCFF}
    .credlink {color: red}
    .corangelink {color: orange}
    .c006400link {color: 006400}
    .cgreenlink {color: green}
    .cblacklink {color: black}
    </style>
    <head>
    <title>""" + cameoxml_filename + """</title>
    </head>
    <body>
    """ + events_body + """
    <script>
    var elements = document.getElementsByTagName('a');
    for(var i = 0, len = elements.length; i < len; i++) {
        elements[i].addEventListener("click", highlightSentence(elements[i].href));
    }
    function highlightSentence(link) {
    }
    </script>
    </body>
    </html>
    """)
    f_o.close()

def get_sentences_and_events(cameo_doc):

    sentenceids_to_events = {}
    for sentence in cameo_doc.sentences:
        events = []
        for event in cameo_doc.events:
            if event.sentence_id == sentence.id:
                events.append(event)
        if events != []:
            sentenceids_to_events[sentence.id] = events

    return sentenceids_to_events

def get_original_text(original_input_file, cameo_doc, sentenceids_to_events, cameoxml_filename):

    annotated_text = ""

    if original_input_file != None:

        f = open(original_input_file)

        original_text = f.read().decode('utf-8')

        prev_end_offset = 0
        for sentence in cameo_doc.sentences:
            char_offsets = sentence.char_offsets.split(':')
            start_offset = int(char_offsets[0])
            end_offset = int(char_offsets[1])
            pre_sentence_content = original_text[prev_end_offset:start_offset].replace('\n','<br>')

            sentence_content = ""
            if len(original_text) >= end_offset:
                sentence_content = original_text[start_offset:end_offset].replace('\n','<br>')
            else:
                sys.exit('Wrong Original Text')

            prev_end_offset = end_offset
            if sentence.id in sentenceids_to_events:
                annotated_text += pre_sentence_content + '<a name="' + sentence.id + '"></a><a target="events" class="cCC00CClink" href="' + cameoxml_filename + '_events.html' + '#' + sentence.id + '"><b>' + sentence_content + '<font size=1><sup>' + sentence.id + '</sup></font></b></a>'
            else:
                annotated_text += pre_sentence_content + sentence_content
        annotated_text += original_text[prev_end_offset:].replace('\n','<br>')

        f.close()

    else:

        for sentence in cameo_doc.sentences:
            if sentence.id in sentenceids_to_events:
                annotated_text += '<a name="' + sentence.id + '"></a><a target="events" class="cCC00CClink" href="' + cameoxml_filename + '_events.html' + '#' + sentence.id + '"><b>' + sentence.contents + '<font size=1><sup>' + sentence.id + '</sup></font></b></a>'
            else:
                annotated_text += sentence.contents
            annotated_text += "<br>"

        # Remove extra line breaks
    annotated_text = re.sub(r'<br>(<br>)+', '<br><br>', annotated_text)

    return annotated_text

def get_events_body(cameo_doc, cameoxml_filename, w_icews_sqlite_db):
    events_body = ""

    # Conect to W-ICEWS sqlite DB
    conn = sqlite3.connect(w_icews_sqlite_db)
    cur = conn.cursor()

    # Parse CAMEO XML file
    for sentence in cameo_doc.sentences:
        if sentence.id in sentenceids_to_events:
            sentence_to_write = '<a name="' + sentence.id + '"></a><b>Sentence ' + sentence.id + '<br><a target="text" class="cCC00CClink" href="' + cameoxml_filename + '_text.html' + '#' + sentence.id + '">' + sentence.contents + '</b></a><br><br>\n'
            events_to_write = ""
            for event in sentenceids_to_events[sentence.id]:
                if event.sentence_id == sentence.id:
                    events_to_write += "<i>Event Type: " + event.type + " -- " + event_code_descriptions[event.type] + "</i><br>\n"
                    for participant in event.participants:
                        cur.execute('SELECT name FROM dict_actors where actor_id=?', (participant.actor_id,))
                        actor_name = cur.fetchone()[0]
                        agent_name = ''
                        if participant.agent_id != '':
                            cur.execute('SELECT name FROM dict_agents where agent_id=?', (participant.agent_id,))
                            agent_name = cur.fetchone()[0]

                        if participant.role == 'Target':
                            events_to_write += "<font style='color:green'>Target: "
                        elif participant.role == 'Source':
                            events_to_write += "<font style='color:red'>Source: "
                        else:
                            events_to_write += "<font>"

                        if agent_name != '':
                            events_to_write += actor_name + " - " + agent_name + "</font><br>\n"
                        else:
                            events_to_write += actor_name + "</font><br>\n"
                    events_to_write += "<br>"
            events_body += sentence_to_write + events_to_write + "<hr>"

    # Close W-ICEWS sqlite DB connection
    cur.close()
    conn.close()
    return events_body

# Get command line arguments
parser = argparse.ArgumentParser(description='Produce an HTML Viewer for a CAMEO_XML file.')

script_dir = os.path.dirname(os.path.realpath(__file__))

parser.add_argument('input', help='The CAMEO_XML file, directory, or list of files you wish to view')
parser.add_argument('output_dir', help='Where the HTML Viewer file(s) should be output')
parser.add_argument('--mode', help='Whether to run on a single file, a directory of files, or a list of files', choices=['file', 'directory', 'filelist'], required=True)
parser.add_argument('--original', help='The document(s) that were originally input to ACCENT (supplied in same mode as the primary input to this script, i.e. a file, a directory, or a list of files). These are used to display the original formatting of documents, which is not preserved in CAMEO XML.')
parser.add_argument('--event_descriptions', help='The path the event-code-descriptions.txt file', default=os.path.join(script_dir, '..', 'icews', 'event_code_descriptions.txt'))
parser.add_argument('--icews_db', help='The path to the ICEWS database that was used to create the CAMEO XML', default=os.path.join(script_dir, '..', 'icews', 'lib', 'database', 'icews.current.sqlite'))

args = parser.parse_args()

if not os.path.exists(args.event_descriptions):
    print "Could not find event_descriptions file, specify by using the --event_descriptions parameter"
    sys.exit(1)
if not os.path.exists(args.icews_db):
    print "Could not find ICEWS database, specify by using the --icews_db parameter"
    sys.exit(1)

event_code_descriptions = get_event_code_descriptions(args.event_descriptions)
mode = args.mode

if not os.path.exists(args.output_dir):
    try:
        os.makedirs(args.output_dir)
    except:
        print "Couldn't make directory: " + args.output_dir
        sys.exit(1)

cameoxml_files = []
original_files = []

if mode == 'file':
    cameoxml_files = [args.input]
    if args.original:
        original_files = [args.original]
elif mode == 'directory':
    cameoxml_files = [os.path.join(args.input, x) for x in sorted(os.listdir(args.input))]
    if args.original:
        print "\nThis mode assumes that the CAMEO XML directory is the result"
        print "  processing the original directory in BBN ACCENT batch mode, where"
        print "  the output for file X is named 'X.cameo.xml'. If this is not the case,"
        print "  please use the 'filelist' mode instead.\n"
        original_files = [os.path.join(args.original, x.replace(".cameo.xml", "")) for x in sorted(os.listdir(args.input))]
elif mode == 'filelist':
    with open(args.input, 'r') as IN:
        cameoxml_files = [x.strip() for x in IN.readlines()]
    if args.original:
        with open(args.original, 'r') as IN:
            original_files = [x.strip() for x in IN.readlines()]

if args.original and len(cameoxml_files) != len(original_files):
    sys.exit('Different number of input documents and original documents')

basenames = []
for i, f in enumerate(cameoxml_files):
    cameoxml_filename = os.path.basename(f)
    if cameoxml_filename in basenames:
        print "Warning: multiple files with the same base name; skipping", f
        continue
    cameo_doc = cameoxml.Document(f)

    original_filename = None
    if args.original:
        original_filename = original_files[i]
        if not os.path.exists(original_filename):
            print "Error: original file %s does not exist;\n  proceeding without original formatting\n" % original_filename
            original_filename = None

    sentenceids_to_events = get_sentences_and_events(cameo_doc)
    text_body = get_original_text(original_filename, cameo_doc, sentenceids_to_events, cameoxml_filename)
    events_body = get_events_body(cameo_doc, cameoxml_filename, args.icews_db)

    write_main_HTML_file(args.output_dir, cameoxml_filename)
    write_text_HTML_file(args.output_dir, cameoxml_filename, text_body)
    write_events_HTML_file(args.output_dir, cameoxml_filename, events_body)
    
    print "Wrote: " + os.path.join(args.output_dir, cameoxml_filename + ".html")
