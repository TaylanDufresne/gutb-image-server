import math
import numpy as np
from PIL import Image
import os
import sys
from gti import read_bed_file
from progress.bar import Bar, ChargingBar

cwd = os.getcwd()
image_path = cwd

background_color_light = 18
background_color_dark = 255
max_pixels = 16383


def parse_alignment_details(line):
    alignment_details_list = line.split(' ')
    alignment_details = {
        "score": float(alignment_details_list[3].split('=')[1].strip()),
        'e_value': float(alignment_details_list[4].split('=')[1].strip()),
        'count': float(alignment_details_list[5].split('=')[1].strip()),
        'type': 'regular' if alignment_details_list[7].strip() == 'plus' else 'flipped',
        'source': alignment_details_list[6].split('&')[0].strip(),
        'target': alignment_details_list[6].split('&')[1].strip(),
        'sourceKey': alignment_details_list[6].split('&')[0].strip()[2:],
        'targetKey': alignment_details_list[6].split('&')[1].strip()[2:],
        'alignmentID': float(alignment_details_list[2].split(':')[0].strip())
    }
    return alignment_details


def parse_link(line):
    link_info = line.split("\t")
    link_dict = {
        "source": link_info[1],
        "target": link_info[2],
        "e_value": float(link_info[3].strip()),
    }
    return link_dict


def only_unique(value, index, self):
    return self.indexOf(value) == index


def read_collinearity_file(filename):
    alignment_list = []
    alignment_buffer = {}

    collinearity_file = open(filename, 'r')
    # Skip the first 11 lines containing MCSCANX information
    for i in range(0, 11):
        next(collinearity_file)
    # Run over remaining lines
    for line in collinearity_file:
        if "Alignment" in line:
            # store the previous alignment in list, and skip for the first iterations since buffer is empty
            if "links" in alignment_buffer:
                alignment_list.append(alignment_buffer)
            alignment_buffer = parse_alignment_details(line)
            alignment_buffer["links"] = []

        # Condition to skip empty lines
        elif len(line.strip()) > 1:
            alignment_buffer["links"].append(parse_link(line))

    collinearity_file.close()

    # Push the last alignment still in the buffer
    alignment_list.append(alignment_buffer)

    # Get the unique list of IDs of all chromosomes or scaffolds that have alignments mapped to them
    unique_id_list = []
    for i in alignment_list:
        if i["source"] not in unique_id_list:
            unique_id_list.append(i["source"])
        if i["target"] not in unique_id_list:
            unique_id_list.append(i["target"])

    final_product = {
        "information": {},
        "alignmentList": alignment_list,
        "uniqueIDList": unique_id_list,
    }
    return final_product


def generate_ortholog_image(bed_file, collinearity_file):
    pixel_width = max_pixels
    print("Parsing files...")
    dataset = read_bed_file(bed_file)
    processed_collinearity = read_collinearity_file(collinearity_file)

    output_directory = bed_file.split("/")[-1].split(".")[0] + "_orthologs"

    if not os.path.isdir(output_directory):
        os.mkdir(output_directory)
    else:
        warning_check = input("\nWarning, directory already exists. Images may be overwritten. Would you like to "
                              "continue? (Y/N)\n")
        if warning_check == "N" or warning_check == "n":
            print("Exiting...")
            exit(0)

    statement = "Generating dark " if dark else "Generating light "

    # Fuck it, hacky fix
    nomenclature = []
    for key in dataset.keys():
        name = ''.join(filter(lambda x: x.isalpha(), key))
        if name not in nomenclature:
            nomenclature.append(name)

    print("Linking orthologs...")
    linking_bar = ChargingBar("Generating Linkages", max=len(processed_collinearity["alignmentList"]))
    for x in processed_collinearity["alignmentList"]:
        # print(x)
        for link in x["links"]:
            for name in nomenclature:
                if name.upper() in link["source"] and name.upper() in link["target"] and link["e_value"] == 0:
                    # Modifying the dataset with the orthologs and their links
                    dataset[x["source"]][link["source"]]["ortholog"] = True
                    dataset[x["source"]][link["source"]]["siblings"].append(link["target"])

                    dataset[x["target"]][link["target"]]["ortholog"] = True
                    dataset[x["target"]][link["target"]]["siblings"].append(link["source"])
        linking_bar.next()
    linking_bar.finish()
    print("Generating Images...")
    image_bar = ChargingBar("Progress", max=len(dataset.keys()))
    for x in dataset.keys():
        chromosome_bar = Bar("Chromosome Progress", max=max_pixels)
        last_bp = max(dataset[x].items(), key=lambda a: a[1]['end'])
        last_bp = last_bp[1]['end']
        # print("Generating " + x + " chromosomal ortholog array with " +
        #       str(last_bp) + " base pairs...")
        temp_list = [False] * (last_bp)
        for gene in dataset[x]:
            if dataset[x][gene]["ortholog"]:
                for i in range(dataset[x][gene]['start'], dataset[x][gene]['end']):
                    temp_list[i] = True
        if temp_list[-1]:
            print("Success!")

        total = pixel_width

        bp_ratio = last_bp / total
        adjustment = round(last_bp / bp_ratio)
        rounded_bp_ratio = round(last_bp / total)

        if bp_ratio != 0:
            # print(statement + x + " chromosomal ortholog image with " +
            #       str(adjustment) + " pixels...")
            # print("Resolution: " + str(rounded_bp_ratio) + " base pairs per pixel")
            new_image_light = Image.new('RGBA', (adjustment, 1))
            new_image_dark = Image.new('RGBA', (adjustment, 1))
            for z in range(0, adjustment):
                alpha = 0
                for k in range(0, rounded_bp_ratio):
                    if temp_list[round(min(z * bp_ratio + k, last_bp - 1))]:
                        alpha += 1
                alpha = int((alpha / bp_ratio) * 255)
                new_image_light.putpixel((z, 0), (
                    background_color_light, background_color_light, background_color_light, alpha))
                new_image_dark.putpixel((z, 0), (
                    background_color_dark, background_color_dark, background_color_dark, alpha))
                chromosome_bar.next()
            chromosome_bar.finish()
            # print("Successfully made track image! Saving...")
            new_image_light.save(output_directory + "/" + x + "_track.webp", "WEBP", lossless=True, quality=100)
            new_image_dark.save(output_directory + "/" + x + "_track_dark.webp", "WEBP", lossless=True, quality=100)
        image_bar.next()
    image_bar.finish()


if __name__ == '__main__':

    # generate_ortholog_image("/home/td/Work/GUOB/guob/public/files/at_coordinate.gff",
    #                         "/home/td/Work/GUOB/guob/public/files/at_vv_collinear.collinearity")
    dark = False
    multiple = False
    if len(sys.argv) < 3:
        print(str(len(sys.argv)) + " arguments given, required: 3")
        print("Usage: python gti bed_file collinearity_file output_directory [-d] ")
        exit(-1)
        ## Image path?

    elif len(sys.argv) == 3:
        cwd = os.getcwd()
        generate_ortholog_image(sys.argv[1], sys.argv[2])
    elif len(sys.argv) > 3:
        print("Usage: python oti bed_file collinearity_file")
