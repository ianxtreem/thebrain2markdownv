import json
import codecs
import io
import html2markdown
import shutil

thoughts_path = "./export/thoughts.json"
links_path = "./export/links.json"
attachments_path = "./export/attachments.json"

# Relations
NOVALUE = 0
CHILD = 1
PARENT = 2
JUMP = 3
SIBLING = 4

# Attachments
INTERNALFILE = 1  # A file embeded in the thought.  Needs to be copied to the thought location
EXTERNALFILE = 2
EXTERNALURL = 3
NOTESV9 = 4
ICON = 5 # If its an icon, we need to rename and move Icon.png in the .data directory.  Prepend with thought name.
NOTESASSET = 6
INTERNALDIRECTORY = 7
EXTERNALDIRECTORY = 8
SUBFILE = 9
SUBDIRECTORY = 10
SAVEDREPORT = 11
MARKDOWNIMAGE = 12

#Type:  the exported type
#SourceType:  what type it was in the brain

# Process the links file
links_json = {}
for line in codecs.open(links_path, "r", "utf-8-sig"):
    link = json.loads(line)
    node_id_a = link["ThoughtIdA"]
    node_id_b = link["ThoughtIdB"]
    if link["Relation"] == CHILD:
        try:
            test = links_json[node_id_a]
        except KeyError:
            links_json[node_id_a] = []

        item = {}
        item["Link"] = link["ThoughtIdB"]
        item["Relation"] = link["Relation"]

        links_json[node_id_a].append(item)

    if link["Relation"] == JUMP:
        # direction A to B
        try:
            test = links_json[node_id_a]
        except KeyError:
            links_json[node_id_a] = []

        item = {}
        item["Link"] = link["ThoughtIdB"]
        item["Relation"] = link["Relation"]

        links_json[node_id_a].append(item)

        
        # direction B to A
        try:
            test = links_json[node_id_b]
        except KeyError:
            links_json[node_id_b] = []

        item = {}
        item["Link"] = link["ThoughtIdA"]
        item["Relation"] = link["Relation"]

        links_json[node_id_b].append(item)
    


# print(links_json)

# loops through attachements.json parsing attachment information into attachments_json 
attachments_json = {}
for line in codecs.open(attachments_path, "r", "utf-8-sig"):
    attachment = json.loads(line)
    node_id = attachment["SourceId"]
    try:
        test = attachments_json[node_id]
    except KeyError:
        attachments_json[node_id] = []

    item = {}
    item["Name"] = attachment["Name"]
    item["Location"] = attachment["Location"]
    item["Type"] = attachment["Type"]
    item["SourceType"] = attachment["SourceType"] #ifb
    item["NoteType"] = attachment["NoteType"] #ifb

    attachments_json[node_id].append(item)

# loop through thoughts.json parsing node data into nodes_json
nodes_json = {}
for line in codecs.open(thoughts_path, "r", "utf-8-sig"):
    node = json.loads(line)
    node_id = node["Id"]
    nodes_json[node_id] = {}
    nodes_json[node_id]["Name"] = node.get("Name")
    nodes_json[node_id]["CreationDateTime"] = node.get("CreationDateTime")
    nodes_json[node_id]["Kind"] = node.get("Kind")

# creates the relationship structure based on links.json file  
# It looks like this just handles one way jump links.  Jumps need to be two ways. ifb
for key, value in nodes_json.items():
    node_id = key
    try:
        for link in links_json[node_id]:
            if link["Relation"] == CHILD:
                try:
                    nodes_json[node_id]["Children"].append(nodes_json[link["Link"]]["Name"])
                except KeyError:
                    nodes_json[node_id]["Children"] = []
                    nodes_json[node_id]["Children"].append(nodes_json[link["Link"]]["Name"])

                try:
                    nodes_json[link["Link"]]["Parents"].append(nodes_json[node_id]["Name"])
                except KeyError:
                    nodes_json[link["Link"]]["Parents"] = []
                    nodes_json[link["Link"]]["Parents"].append(nodes_json[node_id]["Name"])
            if link["Relation"] == JUMP:
                try:
                    nodes_json[node_id]["Jumps"].append(nodes_json[link["Link"]]["Name"])
                except KeyError:
                    nodes_json[node_id]["Jumps"] = []
                    nodes_json[node_id]["Jumps"].append(nodes_json[link["Link"]]["Name"])
            if link["Relation"] == SIBLING:
                try:
                    nodes_json[node_id]["Siblings"].append(nodes_json[link["Link"]]["Name"])
                except KeyError:
                    nodes_json[node_id]["Siblings"] = []
                    nodes_json[node_id]["Siblings"].append(nodes_json[link["Link"]]["Name"])
    except KeyError:
        pass
    
    # This block of code seems to assume that every internal file type is a text file.  
    # This needs to be modified to make internal files saved to disk.  The internal notes is 
    # always in a file called Notes.md.
    # Modify to handle NodeType 5 which is a thought icon.  Also need to make sure that internal
    # images are working.
    try:
        for attachment in attachments_json[node_id]:
            #if attachment["Type"] == INTERNALFILE:
            if attachment["Type"] == INTERNALFILE and attachment["NoteType"] == 4:
                internal_file = "./export/" + node_id + "/" + attachment["Location"]
                text = []
                try:
                    # 
                    for line in io.open(internal_file):
                        text.append(line)
                except UnicodeDecodeError:
                    text = ""

                text = "".join(text)
                #text = html2markdown.convert(text) #ifb notes are in markdown already.  v14. ifb

                try:
                    nodes_json[node_id]["InternalFile"].append(text)
                except KeyError:
                    nodes_json[node_id]["InternalFile"] = []
                    nodes_json[node_id]["InternalFile"].append(text)

            #process none note.md internal files.  ifb
            if attachment["Type"] == INTERNALFILE and attachment["NoteType"] == 0:
                internal_file = "./export/" + node_id + "/" + attachment["Location"]
                #name = value["Name"].replace("/", "-")
                #filename = "./obsidian/" + name + ".md"
                # copy internal_file to "./obsidian"
                try:
                    shutil.copy(internal_file, "./obsidian")
                except:
                    print("Error copying file: ", internal_file)

            # Process the Icons.  ifb
            # Modify the name to be unique. 
            # Prepend a link to the note text
            if attachment["Type"] == ICON and attachment["NoteType"] == 0:
                internal_file = "./export/" + node_id + "/.data/" + attachment["Location"]
                name = attachment["Name"]
                destination = "./obsidian/" + node_id + name
                try:
                    shutil.copy(internal_file, destination)
                except:
                    print("Error copying file: ", internal_file)

                try:
                    nodes_json[node_id]["Icon"].append(node_id + name)
                except KeyError:
                    nodes_json[node_id]["Icon"] = []
                    nodes_json[node_id]["Icon"].append(node_id + name)

            # tbd.  Condition not met in my test files
            if attachment["Type"] == NOTESV9:
                notesv9 = "./export/" + node_id + "/Notes/" + attachment["Location"]
                text = []
                for line in io.open(notesv9):
                    text.append(line)

                text = "".join(text)
                text = html2markdown.convert(text)

                try:
                    nodes_json[node_id]["Notes"].append(text)
                except KeyError:
                    nodes_json[node_id]["Notes"] = []
                    nodes_json[node_id]["Notes"].append(text)

            # Process external files ifb
            if attachment["Type"] == INTERNALFILE and attachment["NoteType"] == 0:
                try:
                    nodes_json[node_id]["ExternalFile"].append(attachment["Location"])
                except KeyError:
                    nodes_json[node_id]["ExternalFile"] = []
                    nodes_json[node_id]["ExternalFile"].append(attachment["Location"])
            
            # Process external URL's.  This works
            if attachment["Type"] == EXTERNALURL:
                try:
                    nodes_json[node_id]["ExternalURL"].append(attachment["Location"])
                except KeyError:
                    nodes_json[node_id]["ExternalURL"] = []
                    nodes_json[node_id]["ExternalURL"].append(attachment["Location"])
            
            # tbd
            if attachment["Type"] == NOTESASSET or attachment["Type"] == MARKDOWNIMAGE:
                try:
                    nodes_json[node_id]["Image"].append(attachment["Location"])
                except KeyError:
                    nodes_json[node_id]["Image"] = []
                    nodes_json[node_id]["Image"].append(attachment["Location"])
    except KeyError:
        pass

# this section writes the thought text, including links to external items. It definately doesn't seem to
# place internal images in the correct place in the text.  Also there is no provision for Icons.  Icon
# processing is handled above and prepended to the text block since that is where the icon should be.
# Things like parrent links, sibling links etc should be added at the end but not anything else.
for _, value in nodes_json.items():
    contents = []
    name = value["Name"].replace("/", "-")
    filename = "./obsidian/" + name + ".md"
    text_file = open(filename, "w")
    if "Icon" in value:
        for attachment in value["Icon"]:
            text_file.write("\n![[" + attachment + "]]")
    if "ExternalURL" in value:
        for attachment in value["ExternalURL"]:
            text_file.write("\n" + attachment)
    if "ExternalFile" in value:
        for attachment in value["ExternalFile"]:
            text_file.write("\n![[" + attachment + "]]\n")
    if "InternalFile" in value:
        for attachment in value["InternalFile"]:
            attachment = attachment.replace(":{", "")
            attachment = attachment.replace(":}", "")
            text_file.write("\n" + attachment)
    if "Notes" in value:
        for attachment in value["Notes"]:
            attachment = attachment.replace(":{", "")
            attachment = attachment.replace(":}", "")
            text_file.write("\n" + attachment)
    if "Image" in value:
        for attachment in value["Image"]:
            text_file.write("\n![[" + attachment + "]]")
    if "Children" in value or "Parents" in value or "Jumps" in value:
        text_file.write("\n\n")
    if "Children" in value:
        text_file.write("\nChildren: ")
        text = ", ".join([str("[[" + item + "]]") for item in value["Children"]])
        text = text.replace("/", "-")
        text_file.write(text)
    if "Parents" in value:
        text_file.write("\nParents: ")
        text = ", ".join([str("[[" + item + "]]") for item in value["Parents"]])
        text = text.replace("/", "-")
        text_file.write(text)
    if "Jumps" in value:
        text_file.write("\nJumps: ")
        text = ", ".join([str("[[" + item + "]]") for item in value["Jumps"]])
        text = text.replace("/", "-")
        text_file.write(text)

    text_file.close()
