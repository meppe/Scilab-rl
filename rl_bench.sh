# This list contains all RLBench environments sorted by their goal-conditions.

DetectedConditionEnvs="close_grill
reach_target
place_shape_in_shape_sorter
put_rubbish_in_bin
take_umbrella_out_of_umbrella_stand
empty_dishwasher
sweep_to_dustpan
straighten_rope
water_plants
take_item_out_of_drawer
put_item_in_drawer
slide_block_to_target
open_grill"
# close_grill is very slow
# empty_dishwasher, take_item_out_of_drawer and put_item_in_drawer are also rather slow
# for some reason, open_grill is not slow

DetectedAndNothingGraspedConditionEnvs="take_cup_out_from_cabinet
setup_checkers
play_jenga
light_bulb_out
meat_on_grill
open_jar
put_groceries_in_cupboard
place_cups
reach_and_drag
take_shoes_out_of_box
take_toilet_roll_off_stand
move_hanger
take_money_out_safe
light_bulb_in
phone_on_base
take_usb_out_of_computer
put_shoes_in_box
take_off_weighing_scales
weighing_scales
insert_usb_in_computer
beat_the_buzz
stack_wine
put_money_in_safe
put_bottle_in_fridge
close_jar
hang_frame_on_hanger
stack_cups
put_umbrella_in_umbrella_stand
take_frame_off_hanger
solve_puzzle
remove_cups
set_the_table
open_oven
place_hanger_on_rack
plug_charger_in_power_supply
put_books_on_bookshelf
take_tray_out_of_oven
meat_off_grill
take_plate_off_colored_dish_rack
unplug_charger
open_wine_bottle
change_clock
put_tray_in_oven
put_toilet_roll_on_stand"
# place_cups, remove_cups fail because they add a condition each time reset() is called
# put_books_on_bookshelf is rather slow

OtherEnvs="put_knife_in_knife_block
toilet_seat_up
slide_cabinet_open_and_place_cups
put_plate_in_colored_dish_rack
lamp_on
close_microwave
change_channel
lamp_off
pick_and_lift
push_buttons
take_lid_off_saucepan
close_fridge
get_ice_from_fridge
put_knife_on_chopping_board
open_fridge
turn_tap
press_switch
open_microwave
push_button
tv_off
stack_blocks
pick_up_cup
empty_container
toilet_seat_down
turn_oven_on
open_door
wipe_desk
screw_nail
close_drawer
tv_on
hannoi_square
hit_ball_with_queue
close_laptop_lid
open_drawer
slide_cabinet_open
hockey
close_door
put_all_groceries_in_cupboard
scoop_with_spatula
open_window
close_box
block_pyramid
pour_from_cup_to_cup
open_box"
# Could not place the task put_plate_in_colored_dish_rack in the scene. This should not happen, please raise an issues on this task.
# pour_from_cup_to_cup also failed with the same error.
for ENV in $DetectedConditionEnvs
do
  ENV="$ENV-state-v0"
  python experiment/train.py env=$ENV algorithm=sac +replay_buffer=her render_args=[['display',1],['none',1]] n_epochs=1 eval_after_n_steps=100 n_test_rollouts=1
done
