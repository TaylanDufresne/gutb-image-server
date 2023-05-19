from PIL import Image
import os
import sys
from progress.bar import Bar, ChargingBar

cwd = os.getcwd()


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


def read_bed_file(filename):
    bed_file = open(filename, 'r')
    dataset = {}
    total_length = 0
    for line in bed_file:
        total_length += 1
        split = line.split('\t')
        chromosome = split[0]
        key = str(split[0]) + "-" + str(split[1]) + "-" + str(split[2])
        start = int(split[1])
        end = int(split[2])
        value = int(split[3])

        stats = {
            "chromosome": chromosome,
            "key": key,
            "start": start,
            "end": end,
            "value": value,
        }
        if chromosome not in dataset.keys():
            dataset[chromosome] = {}
        dataset[chromosome][start] = stats

    bed_file.close()
    return dataset, total_length


def generate_methylation_image(bed_file):
    output_directory = bed_file.split("/")[-1].split(".")[0]

    # Make output directory if it doesn't exist
    if not os.path.isdir(output_directory):
        os.mkdir(output_directory)
    else:
        warning_check = input("\nWarning, directory already exists. Images may be overwritten. Would you like to "
                              "continue? (Y/N)\n")
        if warning_check == "N" or warning_check == "n":
            print("Exiting...")
            exit(0)

    parsed_file = read_bed_file(bed_file)
    dataset = parsed_file[0]
    pixel_width = parsed_file[1]

    background_color_light = 255
    background_color_dark = 18

    overview_bar = ChargingBar("Overall Progress", max=len(dataset.keys()))
    for x in dataset.keys():

        last_bp = max(dataset[x].items(), key=lambda a: a[1]['end'])
        last_bp = last_bp[1]['end']
        number_of_entries = len(dataset[x])

        total = pixel_width

        # Kept this just as a valid check because I'm lazy. Efficient? No. Easy? Yes.
        bp_ratio = last_bp / total
        if bp_ratio != 0:
            heatmap_image_light = Image.new('RGBA', (number_of_entries, 1))
            histogram_image_light = Image.new('RGBA', (number_of_entries, 100))

            heatmap_image_dark = Image.new('RGBA', (number_of_entries, 1))
            histogram_image_dark = Image.new('RGBA', (number_of_entries, 100))
            previous = -1

            placement = 0
            for block in dataset[x]:
                if previous > dataset[x][block]['start']:
                    print("File out of order.")
                    exit(-1)
                previous = dataset[x][block]['start']
                value = dataset[x][block]['value']
                alpha = int(255 * ((100 - value) / 100))
                heatmap_image_light.putpixel((placement, 0), (background_color_light, background_color_light,
                                                              background_color_light, alpha))
                heatmap_image_dark.putpixel((placement, 0), (background_color_dark, background_color_dark,
                                                             background_color_dark, alpha))
                absence = 99 - value
                for n in range(0, 99):
                    if n < absence:
                        histogram_image_light.putpixel((placement, n), (background_color_light, background_color_light,
                                                                        background_color_light, 255))
                        histogram_image_dark.putpixel((placement, n), (background_color_dark, background_color_dark,
                                                                       background_color_dark, 255))
                    else:
                        histogram_image_light.putpixel((placement, n), (background_color_light, background_color_light,
                                                                        background_color_light, alpha))
                        histogram_image_dark.putpixel((placement, n), (background_color_dark, background_color_dark,
                                                                       background_color_dark, alpha))
                placement += 1

            heatmap_image_light.save(
                output_directory + "/" + x + "_heatmap.webp", "webp")
            histogram_image_light.save(
                output_directory + "/" + x + "_histogram.webp", "webp")

            heatmap_image_dark.save(
                output_directory + "/" + x + "_heatmap_dark.webp", "webp")
            histogram_image_dark.save(
                output_directory + "/" + x + "_histogram_dark.webp", "webp")
            overview_bar.next()
    overview_bar.finish()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(str(len(sys.argv)) + " arguments given, required: 2")
        print("Usage: python mti_path bed_file")
        exit(-1)
    elif len(sys.argv) == 2:
        generate_methylation_image(sys.argv[1])
    else:
        print("Usage: python mti_path bed_file")
