#!/usr/bin/env python
# -*- coding: latin-1 -*-
import atexit
import codecs
import csv
import random
from os.path import join

import yaml
from psychopy import visual, event, logging, gui, core

from misc.screen_misc import get_screen_res, get_frame_rate

# GLOBALS
RESULTS = list()  # list in which data will be colected
RESULTS.append(['Participant ID', 'Trial number', 'Trial type', 'correct', 'Displayed flanker', 'Key pressed', 'Reaction time', 'Congurent'])  # ... Results header
trial_no = 0
trial_number = 0
chosen_stim = {}
conf = None
left=["HHH", "KKK","SHS", "SKS", "CHC", "CKC"]
right=["CCC", "SSS", "HSH", "HCH", "KSK", "KCK"]

@atexit.register # allows to save results on exit
def save_beh_results():
    """
    Save results of experiment. Decorated with @atexit in order to make sure, that intermediate
    results will be saved even if interpreter will break.
    """
    with open(join('results', PART_ID + '_' + str(random.choice(range(100, 1000))) + '_beh.csv'), 'w', encoding='utf-8') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()


def read_text_from_file(file_name, insert=''):
    """
    Method that read message from text file, and optionally add some
    dynamically generated info.
    :param file_name: Name of file to read
    :param insert:
    :return: message
    """
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)

def check_exit(keys):
    """
    Check (during procedure) if experimentator doesn't want to terminate.
    """
    global conf

    # if keys exists and it contains EXIT_KEY abort with error
    if keys and conf["EXIT_KEY"] in keys:
        abort_with_error('Experiment finished by user! {} pressed.'.format(conf["EXIT_KEY"]))


def wait_or_exit(frameCount, clock):
    """
    Waits for frameCount to pass.
    """

    # convert frameCount to waitTime in seconds
    waitTime = 1/(conf['FRAME_RATE'])*frameCount
    begin = clock.getTime()

    # wait for reaction key to be pressed 
    awaitedKeys = event.waitKeys(keyList=conf['REACTION_KEYS'], maxWait=waitTime)

    end = clock.getTime()
    timePassed = end - begin

    # convert timePassed to framePassed
    framePassed = timePassed*(conf['FRAME_RATE'])

    # if EXIT_KEY was pressed exit occurs
    check_exit(awaitedKeys)

    # if key was pressed before frameCount passing wait_or_exit occurs again with the remaining frameCount
    if framePassed < frameCount:
        wait_or_exit(frameCount-framePassed, clock)


def wait_or_exit_for(frameCount, clock, reminder, stim, win):
    """
    Waits for frameCount to pass and draws reminder and stimuli.
    """
    for _ in range(frameCount):  # present stimuli

        # wait for reaction key to be pressed 
        awaitedKeys=event.getKeys(keyList=list(conf['REACTION_KEYS']), timeStamped=clock)
        
        if len(awaitedKeys):
           
            key = awaitedKeys[0][0]
            time = awaitedKeys[0][1]
            
            # if EXIT_KEY was pressed exit occurs
            check_exit(key)
            
            return [key], time

        reminder.draw()
        stim.draw()
        win.flip()


def wait_for_key():
    """
    Waits for reaction key to be pressed during REACTION_TIME and returns that key
    """
    awaitedKeys = event.waitKeys(keyList=list(conf['REACTION_KEYS']), maxWait=conf['REACTION_TIME'])
    return awaitedKeys


def show_info(win, file_name, insert=''):
    """
    Clear way to show info message into screen.
    :param win:
    :return:
    """
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='black', text=msg,
                          height=30, wrapWidth=SCREEN_RES['width'])
    msg.draw()
    win.flip()
    awaitedKeys = event.waitKeys(keyList=['f7', 'return', 'space', 'left', 'right'])
    if awaitedKeys == ['f7']:
        abort_with_error(
            'Experiment finished by user on info screen! F7 pressed.')
    win.flip()

def congruentness(displayed_flanker):
    """
    Check if displayed_flanker was congurent.
    """
    congurent=["HHH", "KKK", "CCC", "SSS"]
    if displayed_flanker in congurent:
        return "yes"
    return "no"

def abort_with_error(err):
    """
    Call if an error occured.
    """
    logging.critical(err)
    raise Exception(err)

def chooseFlanker():
    global chosen_stim, left, right
    
    # fill dict chosen_stim
    if len(chosen_stim) == 0:
        for i in left:
            chosen_stim[i] = {"isRight": False, "used": False}
        for i in right:
            chosen_stim[i] = {"isRight": True, "used": False}
    
    unchosen_stims = []
    for key in chosen_stim.keys():
        if chosen_stim[key]["used"] == False:
            unchosen_stims.append(key)
    
    chosen_flanker = random.choice(unchosen_stims)
    chosen_stim[chosen_flanker]["used"] = True
    print("chooseFlanker", chosen_flanker, chosen_stim[chosen_flanker]["isRight"])
    return chosen_flanker, chosen_stim[chosen_flanker]["isRight"]

def main():
    global PART_ID, trial_no, conf, left, right # PART_ID is used in case of error on @atexit, that's why it must be global

    # === Dialog popup ===
    info={'IDENTYFIKATOR': '', u'P\u0141E\u0106': ['M', "K"], 'WIEK': ''}
    dictDlg=gui.DlgFromDict(
        dictionary=info, title='Test flanker\u00F3w')
    if not dictDlg.OK:
        abort_with_error('Info dialog terminated.')

    clock=core.Clock()
    # load config, all params are there
    conf=yaml.load(open('config.yaml', encoding='utf-8'), Loader=yaml.FullLoader)

    # === Scene init ===
    win=visual.Window(list(SCREEN_RES.values()), fullscr=True, monitor='testMonitor', units='pix', screen=0, color=conf['BACKGROUND_COLOR'])
    event.Mouse(visible=False, newPos=None, win=win)  # Make mouse invisible
    FRAME_RATE=get_frame_rate(win)
    
    if len(left)+len(right) != conf["NUMBER_OF_TRIALS"]:
        abort_with_error("Number of trials doesn't equal number of stimuli")

    # check if a detected frame rate is consistent with a frame rate for witch experiment was designed
    # important only if milisecond precision design is used
    if FRAME_RATE != conf['FRAME_RATE']:
        dlg=gui.Dlg(title="Critical error")
        dlg.addText(
            'Wrong no of frames detected: {}. Experiment terminated.'.format(FRAME_RATE))
        dlg.show()
        return None

    PART_ID=info['IDENTYFIKATOR'] + info[u'P\u0141E\u0106'] + info['WIEK']
    logging.LogFile(join('results', PART_ID + '.log'), level=logging.INFO)  # errors logging
    logging.info('FRAME RATE: {}'.format(FRAME_RATE))
    logging.info('SCREEN RES: {}'.format(SCREEN_RES.values()))
    
    # === Training ===
    show_info(win, join('.', 'messages', 'hello.txt'))
    
    trial_no += 1

    show_info(win, join('.', 'messages', 'before_training.txt'))
    
    for trial_number in range(conf['NUMBER_OF_TRIALS']):
        
        # returns list of parameters from run_trial
        correct, key_pressed, random_flanker, reaction_time = run_trial(win, conf, clock, False)
        correctness="Poprawnie" if correct else "Niepoprawnie"
        
        # appends results from training session
        RESULTS.append([PART_ID, trial_no, 'training', correctness, random_flanker, key_pressed, reaction_time, congruentness(random_flanker)])

        # show correctness
        correctnessText=visual.TextStim(win, text=correctness, height=50, color=conf['STIM_COLOR'])
        correctnessText.draw()

        win.flip()

        # waits for AFTER_TRAINING_TIME to pass
        wait_or_exit(conf["AFTER_TRAINING_TIME"], clock)

        win.flip()

        trial_no += 1

    # === Experiment ===
    show_info(win, join('.', 'messages', 'before_experiment.txt'))

    for block_no in range(conf['NO_BLOCKS']):
        for _ in range(conf['NUMBER_OF_TRIALS']):

            # returns list of parameters from run_trial
            correct, key_pressed, random_flanker, reaction_time = run_trial(win, conf, clock, True)
            correctness="Poprawnie" if correct else "Niepoprawnie"

            # appends results from training session
            RESULTS.append([PART_ID, trial_no, 'experiment', correctness, random_flanker, key_pressed, reaction_time, congruentness(random_flanker)])
            
            trial_no += 1
        
        if block_no < conf['NO_BLOCKS']-1:
            show_info(win, join('.', 'messages', 'break.txt'))

    # === Cleaning time ===
    logging.flush()
    show_info(win, join('.', 'messages', 'end.txt'))
    win.close()

def run_trial(win, conf, clock, repeating):
    """
    Prepare and present single trial of procedure.
    Input (params) should consist all data need for presenting stimuli.
    If some stimulus (eg. text, label, button) will be presented across many trials.
    Should be prepared outside this function and passed for .draw() or .setAutoDraw().

    All behavioral data (reaction time, answer, etc. should be returned from this function)
    """

    global left, right
    
    # random with repeating
    if repeating:
        # choose random number    
        randomIsRight = random.randrange(2)
        if randomIsRight == 1:
            random_flanker=right[random.randrange(0, len(right))]
        else:
            random_flanker=left[random.randrange(0, len(left))]
    
        stim = visual.TextStim(win, text=random_flanker, height=100, color=conf['STIM_COLOR'])

    # random without repeating
    else:
        random_flanker, randomIsRight = chooseFlanker()
        
        stim = visual.TextStim(win, text=random_flanker, height=100, color=conf['STIM_COLOR'])
    
    fix_cross = visual.TextStim(win, text='+', height=100, color=conf['FIX_CROSS_COLOR'])
    reminder = visual.TextStim(win, wrapWidth=1920, text='H,K - strza\u0142ka w lewo           S,C - strza\u0142ka w prawo', 
    height=30, bold=True, color=conf['REMINDER_COLOR'], alignText='center', pos=(0,300))

    # draw cross
    drawCross(win, fix_cross, reminder)

    # waits for FIX_CROSS_TIME to pass
    wait_or_exit(conf['FIX_CROSS_TIME'], clock)

    # === Start trial ===
    # This part is time-crucial. All stims must be already prepared.
    # Only .draw() .flip() and reaction related stuff goes there.
    event.clearEvents()

    # make sure, that clock will be reset exactly when stimuli will be drawn
    win.callOnFlip(clock.reset)
    
    # present stimuli with reminder
    awaitedKeys, reaction_time = wait_or_exit_for(conf['STIM_TIME'], clock, reminder, stim, win)

    # default values
    key_pressed='no_key'
    correct = False

    # checks keys in awaitedKeys and if they are correct
    for key_pressed in awaitedKeys:
        if (randomIsRight and key_pressed == 'right') or (not randomIsRight and key_pressed == 'left'):
            correct = True
        break
       
    return correct, key_pressed, random_flanker, round(reaction_time*1000)  # return all data collected during trial


def drawCross(win, fix_cross, reminder):
    """
    Draws cross and reminder
    """
    fix_cross.draw()
    reminder.draw()
    win.flip()

if __name__ == '__main__':
    PART_ID=''
    SCREEN_RES=get_screen_res()
    main()
