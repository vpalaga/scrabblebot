import time
#from wsgiref.util import request_uri
import cv2
#from setuptools.unicode_utils import try_encode
#from pipenv.pep508checker import implementation_name
from tqdm import tqdm

from functions import alg, cam_mark, data as d, image as img, shit as sh
from functions.movement import Movement
from functions.config import Constants

Mov = Movement()
s = alg.Scrabble()

def shit(frame, i:int, bw=None) -> str | None:

    """
    Shit stands for:
        Swift
        High-res.
        Image
        Transformer
    """

    resized = sh.resize(frame)
    black_prc = sh.get_black_pixel_percentage(resized, bw=bw)

    if sh.is_letter(black_prc):

        if Constants.Test.testing_mode:
            cv2.imshow(f"letter {i}", frame)
            cv2.waitKey(Constants.Image.imshow_loadtime)

        letter = sh.extract_letter(resized)
        # print(letter)
        d.add_black_letter_val(black_prc)
        return letter
    return None


def get_grid():
    print("->Frame")
    transformed_frame, original_frame = img.get_transformed_frame()

    if Constants.Test.testing_mode:
        cv2.imshow("cropped", transformed_frame)
        cv2.waitKey(Constants.Image.imshow_loadtime)

    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    parameters = cv2.aruco.DetectorParameters()

    # Create the ArUco detector
    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

    cam_mark.get_hand_mark(original_frame, detector)

    # cv2.imshow("trans", transformed_frame)
    print("splitting frame...")
    frames = img.split_into_grid(transformed_frame, Constants.rows, Constants.cols)

    print("selecting frames...")
    frames = img.select_frames(frames)

    # preform a check
    if len(frames) == 157:
        print("Frame Selection : OK")
    else:
        print("Error in split or select: ERROR")
        return  # add a return point IDK

    print("->transforming frames to string...")
    letters = []

    bw = None  # declare bw
    # can use adaptive lightning

    gray = cv2.cvtColor(transformed_frame, cv2.COLOR_BGR2GRAY)
    # cv2.imshow("gray", gray)

    if Constants.Image.use_adaptive_lightning:
        bw = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,  # neighborhood size
            C=2  # constant subtracted from mean
        )

    prc_of_black_view = sh.get_black_pixel_percentage(gray, d=False)

    mid = d.clac_midpoint(d.load(Constants.System.json_path_black_vals))

    print(f"->mid point: {round(mid, ndigits=2)}")
    print(f"->percent of black in the whole frame: {round(prc_of_black_view, ndigits=2)}")
    print("")
    i = 0
    for frame in tqdm(frames, desc="img to str"):  # use tqdm to crate a loading bar

        letters.append(shit(frame, i, bw=bw))  # use network
        i += 1
    print("")
    print("transforming into a dict")

    choose, grid = img.transform_list(letters)
    return grid, choose


def best_word(grid, choose, played_moves):

    rev_grid = alg.reverse_grid(grid)

    best_move, _ = alg.eval_moves(s.all_possible_moves(rev_grid, choose, played_moves))

    # detect if there aren't any available words

    try:
        _ = best_move[0]  # try to get the word
    except TypeError:
        print("caught")
        return 1  # code catch

    return best_move


def grab_letter(letter_pos) -> None:
    Mov.move_to_piece(14, 10)
    time.sleep(0.5)
    letter_x_pos = letter_pos * 2  # gaps between holders

    Mov.move_to_piece(letter_x_pos, 10)

    Mov.open()
    time.sleep(0.5)

    Mov.move_to_piece(letter_x_pos, 11.5)  # slide on to the tile

    Mov.close()
    time.sleep(0.5)

    Mov.move_to_piece(letter_x_pos, 10)  # move out


def build_word(move_tuple, choose: list) -> str | None:  # depending on if the bot lost or not

    letters_dict = move_tuple[3]

    for (x, y), letter in letters_dict.items():
        letter_pos = choose.index(letter)

        grab_letter(letter_pos)

        Mov.move_to_piece(x, y)
        Mov.open()

        Mov.ret()  # return to start and calib


def plot_word(move_tuple: tuple, grid:dict) -> None:

    letters_dict = move_tuple[3]

    # invert here???



    for (x, y), letter in letters_dict.items():
        y = img.invert(y, Constants.rows)


        grid[(x, y)] = letter.upper()  # add the letter to the main dict


def play(played_moves):
    tried_times = 0

    if Constants.Image.transform_img_times < 1:
        d.log("transform times if lower than 1: unable to transform any images", t=1)

        return
    choose, grid = [], {}  # set up data so fucking Idea doesn't give me any warnings :D


    while tried_times != Constants.Image.try_times_to_recognise:
        for _ in range(Constants.Image.transform_img_times):
            # save data to a json file and compare at the end to output a val
            grid, choose = get_grid()
            d.add_grid(grid, choose)

        err_g, choose = d.compare_grids()
        d.log(f"grid error: {err_g}", f"fixed choose: {choose}")

        if Constants.Image.check_multiple_times:
            letters_amt = 0
            for letter in choose:  # check if all choose letters are existing
                if letter is not None:
                     letters_amt += 1

            can = False
            if letters_amt == 7:
                can = True

            if err_g == 0 and can:
                print("resetting grid")
                d.reset_grids()

                img.show_grid(grid, choose)
                break

            else:
                d.log(f"failed to recognise the grid, i: {tried_times}", t=1)
                d.reset_grids() # reset the json with grids
                print("trying again...")
                tried_times += 1
        else:
            # don't check multiple times and just return
            d.reset_grids()

            img.show_grid(grid, choose)
            break

    if tried_times >= Constants.Image.try_times_to_recognise:
        d.log(f"failed to rec the grid {Constants.Image.try_times_to_recognise} times giving up", t=2)
        print("giving up...")
    # print(grid)
    # print(choose)

    img.show_grid(grid, choose)

    if not Constants.Test.testing_mode:
        for letter in choose:  # check if all choose letters are existing
            if letter is None:
                return 2
    else:
        if len(Constants.Test.choose)  ==  7:
            choose = Constants.Test.choose  # replace choose with preset letters

    word = best_word(grid, choose, played_moves)
    print("word")
    d.log("word:", word)
    print(word)

    if word == 1:
        return 1

    plot_word(word, grid)
    img.show_grid(grid)

    played_moves.append(word[0])  # add word to played moves
    #build_word(word, choose)

    return 0
