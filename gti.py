import math
from PIL import Image
import os
import sys
from progress.bar import Bar, ChargingBar

cwd = os.getcwd()

background_color_light = 255
background_color_dark = 18
max_pixels = 16383


def read_bed_file(filename):
    bed_file = open(filename, 'r')
    dataset = {}
    total_length = 0
    for line in bed_file:
        total_length += 1
        split = line.split('\t')
        chromosome = split[0]
        key = split[1]
        start = int(split[2])
        end = int(split[3])

        stats = {
            "chromosome": chromosome,
            "key": key,
            "start": start,
            "end": end,
            "ortholog": False,
            "siblings": [],
        }
        if chromosome not in dataset.keys():
            dataset[chromosome] = {}
        dataset[chromosome][key] = stats

    bed_file.close()
    return dataset


def generate_multiple_tracks(last_bp, total, chromosome, temp_list, output_directory):
    total_images = math.ceil((last_bp / 60) / total)
    bar = Bar(chromosome + " chromosome", max=total_images)

    total = max_pixels
    increments = total * 60

    for needed_image in range(0, total_images):

        if needed_image == total_images - 1:
            total = last_bp % total

        new_image_light = Image.new('RGBA', (total, 1))
        new_image_dark = Image.new('RGBA', (total, 1))

        # Iterating over the bp positions covered by the image
        for pixel in range(0, total):

            full = False

            # Don't proceed past the end of the array
            if needed_image * increments + pixel * 60 >= last_bp - 1:
                break
            for base_pair in range(0, 60):
                # Additional check not proceeding past the end of the array
                if (needed_image * increments) + (pixel * 60) + base_pair >= last_bp - 1:
                    break
                # If a gene at any location covered by the resolution, we don't need to place a pixel
                if temp_list[(needed_image * increments) + (pixel * 60) + base_pair]:
                    full = True
                    break

            # Otherwise, place a pixel
            if not full:
                new_image_light.putpixel((pixel, 0),
                                         (background_color_light, background_color_light, background_color_light, 255))
                new_image_dark.putpixel((pixel, 0),
                                        (background_color_dark, background_color_dark, background_color_dark, 255))

        new_image_light.save(output_directory + "/" + chromosome + "_" + str(needed_image) + ".webp",
                             "WEBP")
        new_image_dark.save(output_directory + "/" + chromosome + "_" + str(needed_image) + "_dark.webp",
                            "WEBP")

        bar.next()

    bar.finish()


def generate_single_track(last_bp, total, temp_list, chromosome, output_directory):
    bp_ratio = last_bp / total
    adjustment = round(last_bp / bp_ratio)
    rounded_bp_ratio = round(last_bp / total)

    if math.floor(last_bp / total) != 0:
        print(f"Generating {chromosome} image with " +
              str(adjustment) + " pixels...")
        print("Resolution: " + str(rounded_bp_ratio) + " base pairs per pixel")
        new_image_light = Image.new('RGBA', (adjustment, 1))
        new_image_dark = Image.new('RGBA', (adjustment, 1))
        bar = Bar(chromosome + " chromosome", max=adjustment)
        for z in range(0, adjustment):
            alpha = 0
            for k in range(0, rounded_bp_ratio):
                if temp_list[round(min(z * bp_ratio + k, last_bp - 1))]:
                    alpha += 1
            alpha = int(255 - (alpha / bp_ratio) * 255)
            new_image_light.putpixel((z, 0),
                                     (background_color_light, background_color_light, background_color_light, alpha))
            new_image_dark.putpixel((z, 0),
                                    (background_color_dark, background_color_dark, background_color_dark, alpha))
            bar.next()

        new_image_light.save(output_directory + "/" + chromosome + "_track.webp",
                             format="WEBP", lossless=True, quality=100)
        new_image_dark.save(output_directory + "/" + chromosome + "_track_dark.webp",
                            format="WEBP", lossless=True, quality=100)


def generate_image(filename, output_directory=None, dark=False, multiple=False):
    pixel_width = max_pixels
    print()

    output_directory = filename.split("/")[-1].split(".")[0]

    # Make output directory if it doesn't exist
    if not os.path.isdir(output_directory):
        os.mkdir(output_directory)
    else:
        warning_check = input("\nWarning, directory already exists. Images may be overwritten. Would you like to "
                              "continue? (Y/N)\n")
        if warning_check == "N" or warning_check == "n":
            print("Exiting...")
            exit(0)

    dataset = read_bed_file(filename)

    statement = "Generating dark " if dark else " Generating light "

    # The GUTB is changing the colors of the track images by modifying the background color,
    # so this is actually generating a track negative - invisible pixels at a gene, and
    # background color at not-gene locations

    keys = list(dataset.keys())

    # Just generating chromosome tracks, so need to remove scaffolds
    keys = [i for i in keys if "Scaffold" not in i]

    overview_bar = ChargingBar("Overall Progress", max=len(keys))
    for x in keys:
        last_bp = max(dataset[x].items(), key=lambda a: a[1]['end'])
        last_bp = last_bp[1]['end']

        # Generating a list of every bp position. Efficient? No. Accurate? You bet.
        temp_list = [False] * last_bp
        for gene in dataset[x]:
            for i in range(dataset[x][gene]['start'], dataset[x][gene]['end']):
                temp_list[i] = True

        total = pixel_width

        # In reality a resolution of 60 bp/pixel seems to still be higher than necessary
        increments = total * 60

        # This branch is used for higher resolution zoomed in images, generating multiple tracks
        # that end up stacked side by side
        # if multiple:

        generate_multiple_tracks(last_bp, total, x, temp_list, output_directory)
        # total_images = math.ceil((last_bp / 60) / total)
        # bar = Bar(x + " chromosome", max=total_images)
        #
        # for needed_image in range(0, total_images):
        #
        #     total = pixel_width
        #
        #     if needed_image == total_images - 1:
        #         total = last_bp % total
        #
        #     new_image = Image.new('RGBA', (total, 1))
        #
        #     # Iterating over the bp positions covered by the image
        #     for pixel in range(0, total):
        #
        #         full = False
        #
        #         # Don't proceed past the end of the array
        #         if needed_image * increments + pixel * 60 >= last_bp - 1:
        #             break
        #         for base_pair in range(0, 60):
        #             # Additional check not proceeding past the end of the array
        #             if (needed_image * increments) + (pixel * 60) + base_pair >= last_bp - 1:
        #                 break
        #             # If a gene at any location covered by the resolution, we don't need to place a pixel
        #             if temp_list[(needed_image * increments) + (pixel * 60) + base_pair]:
        #                 full = True
        #                 break
        #
        #         # Otherwise, place a pixel
        #         if not full:
        #             new_image.putpixel((pixel, 0), (background_color, background_color, background_color, 255))
        #
        #     suffix = f"track_dark_{needed_image}.webp" if dark else f"track_{needed_image}.webp"
        #
        #     if output_directory:
        #         new_image.save(output_directory + "/" + x + "_" + str(int(pixel_width / 1000)) + "K_" + suffix,
        #                        "WEBP")
        #     else:
        #         new_image.save(cwd + "/" + x + "_" + str(int(total / 1000)) + "K_" + suffix, "WEBP")
        #
        #     bar.next()
        #
        # bar.finish()
        # overview_bar.next()

        # This branch is used to generate a single image of the entire track
        # else:

        generate_single_track(last_bp, total, temp_list, x, output_directory)
        print("\n")
        # bp_ratio = last_bp / total
        # adjustment = round(last_bp / bp_ratio)
        # rounded_bp_ratio = round(last_bp / total)
        #
        # if math.floor(last_bp / total) != 0:
        #     print(statement + x + " chromosomal image with " +
        #           str(adjustment) + " pixels...")
        #     print("Resolution: " + str(rounded_bp_ratio) + " base pairs per pixel")
        #     new_image = Image.new('RGBA', (adjustment, 1))
        #     bar = Bar(x + " chromosome", max=adjustment)
        #     for z in range(0, adjustment):
        #         alpha = 0
        #         for k in range(0, rounded_bp_ratio):
        #             if temp_list[round(min(z * bp_ratio + k, last_bp - 1))]:
        #                 alpha += 1
        #         alpha = int(255 - (alpha / bp_ratio) * 255)
        #         new_image.putpixel((z, 0), (background_color, background_color, background_color, alpha))
        #         bar.next()
        #     suffix = "track_dark.webp" if dark else "track.webp"
        #     if output_directory:
        #         new_image.save(output_directory + "/" + x + "_" + str(int(total / 1000)) + "K_" + suffix,
        #                        format="WEBP", lossless=True, quality=100)
        #         # new_image.save(output_directory + "/" + x + "_" + str(int(total / 1000)) + "K_" + suffix, "PNG")
        #
        #     else:
        #         # new_image.save(cwd + "/" + x + "_" + str(int(total / 1000)) + "K_" + suffix, "PNG")
        #         new_image.save(cwd + "/" + x + "_" + str(int(total / 1000)) + "K_" + suffix, format="WEBP")
        overview_bar.next()
    overview_bar.finish()


if __name__ == '__main__':

    output_dir = None

    if len(sys.argv) < 2:
        print(f"\n{str(len(sys.argv) - 1)} arguments given, required: 1")
        print("Usage: python gti_path filename ")
        exit(-1)

    elif len(sys.argv) == 2:
        generate_image(sys.argv[1])

    else:
        print("Usage: python gti_path filename [output_directory] [-d -m] ")
        exit(-1)
