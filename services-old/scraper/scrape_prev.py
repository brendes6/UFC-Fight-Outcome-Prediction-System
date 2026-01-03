import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.parser import parse
import requests
from . import data_cleaning
import os
from google.cloud import firestore 
is_upcoming = False
is_most_recent = True



def scrape_previous_fights():
    response = requests.get('http://ufcstats.com/statistics/events/completed')

    bs = BeautifulSoup(response.content, "html.parser")

    rows = bs.find_all("a", href=True)


    url = ""

    count = 0

    for row in rows:
        href = row['href']

        if "event-details" in href:
            count += 1
            if count == 2:
                url = href
                break
    
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    ufc_master_relative_path = os.path.join(current_script_dir, "ufc-master.csv")
    temp_df = pd.read_csv(ufc_master_relative_path)

    column_list = temp_df.columns

    df = pd.DataFrame(columns=column_list)
    html=urlopen(url)

    bs=BeautifulSoup(html, 'html.parser')

    ###HERE WE ARE GOING TO GET A LIST 

    did_red_lose_list = []
    winner_list = []
    fight_links = bs.find_all('a', {'class':'b-flag'})
    prev_link = ''
    if is_upcoming:
        fight_links = bs.find_all('tr')
        fight_count = len(fight_links) - 1
        for n in range(fight_count):
            did_red_lose_list.append(True)
            winner_list.append('Blue')
            
    else:    
        for n in range(len(fight_links)):

            link = (fight_links[n].attrs['href'])

            if prev_link == link:          #This happens in draws
                pass
            else:
                #Go to the page and figure out who won.
                temp_html = urlopen(link)
                bs_temp = BeautifulSoup(temp_html, 'html.parser')
                fight_result = bs_temp.find('i', {'class':'b-fight-details__person-status'}).get_text().strip()
                if fight_result == 'L':
                    did_red_lose_list.append(True)
                    winner_list.append('Blue')
                elif fight_result == 'D':
                    did_red_lose_list.append(False)
                    winner_list.append('Draw')
                elif fight_result == 'NC':
                    did_red_lose_list.append(False)
                    winner_list.append('No Contest')
                else:
                    did_red_lose_list.append(False)
                    winner_list.append('Red')
                #print(fight_result.get_text())
            prev_link = link

    fights = bs.find_all('td', {'class':'b-fight-details__table-col l-page_align_left'})


    f_count = 0
    fighters_raw = []
    weight_classes_raw = []


    for f in fights:
        
        if f_count%3 == 0 :
            fighters_raw.append(f)
        if f_count%3 == 1:
            weight_classes_raw.append(f)

        f_count=f_count+1


    red_fighter_list = []
    blue_fighter_list = []
    weight_class_list = []

    if is_most_recent:
        for f in fighters_raw:
            temp_fighters = f.find_all('p')
            temp_links = f.find_all('a')
            red_fighter_list.append([temp_fighters[0].get_text().strip(),
                                    temp_links[0].attrs['href']])
            blue_fighter_list.append([temp_fighters[1].get_text().strip(),
                                    temp_links[1].attrs['href']])
    else:
        for f in fighters_raw:
            temp_fighters = f.find_all('p')
            temp_links = f.find_all('a')
            blue_fighter_list.append([temp_fighters[0].get_text().strip(),
                                    temp_links[0].attrs['href']])
            red_fighter_list.append([temp_fighters[1].get_text().strip(),
                                    temp_links[1].attrs['href']])


    for w in weight_classes_raw:
        temp_wc = w.find_all('p')
        weight_class_list.append(temp_wc[0].get_text().strip())

    ###################################################################
    #Insert R_fighter and B_fighter
    #Let's start entering data into the dataframe!
    for i in range(len(red_fighter_list)):
        if did_red_lose_list[i]:
            df_temp = pd.DataFrame({'RedFighter': blue_fighter_list[i][0],
                            'BlueFighter': red_fighter_list[i][0]},
                            index=[i]) 
        else:
            df_temp = pd.DataFrame({'RedFighter': red_fighter_list[i][0],
                            'BlueFighter': blue_fighter_list[i][0]},
                            index=[i]) 
            

        df = pd.concat([df, df_temp])
        


    ##################################################################
    #Let's get the date, and location
    date_raw = bs.find_all('li', {'class':'b-list__box-list-item'})
    child_count=0
    for dr in date_raw:
        temp_count=0
        for child in dr.children:
            #print(child.string)
            #print(temp_count, child_count)
            if ((temp_count == 2) & (child_count == 0)):
                raw_date = (child.string.strip())
            if ((temp_count == 2) & (child_count == 1)):
                location = (child.string.strip())
                
            temp_count = temp_count+1

        child_count = child_count+1


    formatted_date = datetime.strptime(raw_date, "%B %d, %Y")
    date_datetime = formatted_date

    #The pound sign removes the leading 0.
    formatted_date=(formatted_date.strftime("%m/%e/%Y"))
    df['Date'] = formatted_date
    df['Location'] = location


    #################################################################
    #Let's get the country
    split_location = location.split(',')
    country = split_location[len(split_location)-1]
    #print(country.strip())
    country=country.strip()
    df['Country'] = country



    df['WeightClass']=weight_class_list



    ##################################################################
    #Set title_bout
    #THIS NEEDS TO BE UPDATED WHEN WE HAVE AN ACTUAL TITLE FIGHT
    #IT HAS TO DO WITH AN IMAGE NEXT TO THE WEIGHT CLASS.  SO WE CAN
    #TIE THIS INTO HOW WE DETERMINE THE WEIGHT CLASS
    number_of_fights = len(weight_class_list)
    title_fight_list = []
    title_fight_raw = bs.find_all('tr', {'class':'b-fight-details__table-row'})
    skip_row = True
    for f in title_fight_raw:
        if skip_row:
            skip_row = False
        else:
            #print(f)
            f = str(f)
            #print(f)
            if f.find('belt.png') > -1:
                title_fight_list.append(True)
            else:
                title_fight_list.append(False)
    df['TitleBout'] = title_fight_list



    ##################################################################
    #Set Gender... We can use the weight_class_list for this
    #How this works is we look at the weight class name.  If the first
    #word is "Women's" we are dealing with a FEMALE fight.  Otherwise
    #MALE
    gender_list = []
    for wc in weight_class_list:
        if wc.split(' ')[0] == "Women's":
            gender_list.append('FEMALE')
        else:
            gender_list.append('MALE')

    df['Gender'] = gender_list



    ##################################################################
    #Determine the number of rounds.  First check for title fight.
    #All title fights are 5 rounds.  The main event is also 5 rounds.

    round_list = []
    for z in range(number_of_fights):
        if(title_fight_list[z]==True):
            round_list.append(5)
        else:
            round_list.append(3)
            
    round_list[0] = 5

    #print(round_list)

    df['NumberOfRounds'] = round_list

    #################################################################
    #################################################################
    #Let's get the finish and finish details
    if is_most_recent:
        finish_list = []
        finish_details_list = []

        temp_list = bs.find_all('td', {'class':'b-fight-details__table-col l-page_align_left'})


        count = 0
        for t in temp_list:
            if (count+1) % 3 == 0:
                #There are 2 paragraphs here.  One with the finish.  The other with the 
                temp_finish_list = t.find_all('p')
                #print(count)
                #print(t)
                finish_list.append(temp_finish_list[0].get_text().strip())
                finish_details_list.append(temp_finish_list[1].get_text().strip())
            count = count+1



        finish_round_list = []
        time_list = []
        
        temp_list = bs.find_all('td', {'class':'b-fight-details__table-col'})
        

        
        count = 0
        for t in temp_list:
            #print(f"COUNT: {count}")
            #print(t)
        
            if (count) % 10 == 8:
                #There are 2 paragraphs here.  One with the finish.  The other with the 
                #print(count)
                #print(t)
                finish_round_list.append(t.get_text().strip())
                #finish_details_list.append(temp_finish_list[1].get_text().strip())
            elif (count) % 10 == 9:
                time_list.append(t.get_text().strip())
            count = count+1



    #################################################################
    #################################################################


    #################################################################
    #Now we need access to the fighter pages!

    #First let's save them all so we don't have to constantly access them


    #REVERT BEFORE GOING LIVE

    red_count = 0
    for f in red_fighter_list:
        #print(f[1][7:])
        
        html= urlopen(f[1])
        bs = BeautifulSoup(html.read(), 'html.parser')
        with open(os.path.join(current_script_dir, f'fighter_pages/r{red_count}.html'), "w", encoding='utf-8') as file:
            file.write(str(bs))
    

        red_count+=1

    blue_count = 0
    for f in blue_fighter_list:
        #print(f[1][7:])
        
        html= urlopen(f[1])
        bs = BeautifulSoup(html.read(), 'html.parser')
        with open(os.path.join(current_script_dir, f'fighter_pages/b{blue_count}.html'), "w", encoding='utf-8') as file:
            file.write(str(bs))
    

        blue_count+=1


    #Find the current lose and win streaks
    blue_fighter_win_streak = []
    blue_fighter_lose_streak = []
    red_fighter_win_streak = []
    red_fighter_lose_streak = []
    blue_draw_list = []
    red_draw_list = []
    blue_strike_list = []
    red_strike_list = []
    blue_strike_acc_list = []
    red_strike_acc_list = []
    sub_list = []
    td_list = []
    red_sub_list = []
    red_td_list = []
    td_acc_list = []
    red_td_acc_list = []
    red_fighter_longest_win_streak = []
    blue_fighter_longest_win_streak = []
    blue_total_losses = []
    red_total_losses = []
    blue_total_rounds = []
    red_total_rounds = []
    blue_title_bouts = []
    red_title_bouts = []
    blue_total_maj_dec = []
    red_total_maj_dec = []
    blue_total_split_dec = []
    red_total_split_dec = []
    blue_total_un_dec = []
    red_total_un_dec = []
    blue_total_ko = []
    red_total_ko = []
    blue_total_sub = []
    red_total_sub = []
    blue_total_wins = []
    red_total_wins = []
    stance_list = []
    height_list = []
    reach_list = []
    weight_list = []
    red_stance_list = []
    red_height_list = []
    red_reach_list = []
    red_weight_list = []
    blue_age_list = []
    red_age_list = []

    z = 0


    for z in range(number_of_fights):
        #print("new fight")
        #print(did_red_lose_list[z])
        #If red lost these are flipped
        if(did_red_lose_list[z]):
            b_fighter_file=open(os.path.join(current_script_dir, f'fighter_pages/r{z}.html'), "r")
        else:
            b_fighter_file=open(os.path.join(current_script_dir, f'fighter_pages/b{z}.html'), "r")
            
        blue_soup=BeautifulSoup(b_fighter_file.read(), 'html.parser')
        
        
        
        
        
        
        
        
        ###We need to deal with removing historic fights
        ###Maybe just make a date list????
        
        
        
        
        
        
        
        
        blue_results_raw = blue_soup.find_all('i',{'class':'b-flag__text'})
        blue_rounds_raw = blue_soup.find_all('p', {'class':'b-fight-details__table-text'})
        #print(blue_rounds_raw)
        ################################################################
        #Blue Total rounds fought
        #Round totals are on 21, 38, 55, 72... etc...
        #So that is (count - 4) % 17 = 0
        
        
        #We need to redo this whole thing.
        blue_rounds_raw = blue_soup.find_all('tr', {'class':'b-fight-details__table-row'})
        #print(f"Fight rows: {len(blue_fight_dates_raw)}")
        blue_round_count = 0
        for row_temp in blue_rounds_raw:
            pos_dates = row_temp.find_all('p', {'class': 'b-fight-details__table-text'})
            if len(pos_dates) > 16:
                pos_date = (pos_dates[12].get_text().strip())
                event_date_parsed = parse(formatted_date)
                fight_date_parsed = parse(pos_date)
                if fight_date_parsed < event_date_parsed:
                    blue_round_count = blue_round_count + int(pos_dates[15].get_text().strip())

        
        blue_total_rounds.append(blue_round_count)
        ################################################################
        #Test to find fight date
        dates_list = []
        dates_list_red = []
        blue_fight_dates_raw = blue_soup.find_all('tr', {'class':'b-fight-details__table-row'})
        #print(f"Fight rows: {len(blue_fight_dates_raw)}")
        for row_temp in blue_fight_dates_raw:
            pos_dates = row_temp.find_all('p', {'class': 'b-fight-details__table-text'})
            if len(pos_dates) > 16:
                dates_list.append(pos_dates[12].get_text().strip())

        
        
        ###############################################################
        #Blue total title bouts.  We are looking for 'belt.png'
        title_bout_count = 0
        
        #print(blue_soup)
        title_bout_count = str(blue_soup).count('belt.png')
        #print(title_bout_count)
        #If the upcoming fight is a title bout we need to subtract 1
        if(df.iloc[z]['TitleBout']):
            title_bout_count -= 1
        blue_title_bouts.append(title_bout_count)
            
        
        
        
        
        
        ###############################################################
        







        ################################################################
        #Determine the type of win for BLUE
        temp_count = 0
        for b in blue_rounds_raw:
            #print(temp_count)
            #print(b.get_text())
            temp_count+=1
            
        #OK so it lists win or loss at 6, 23, 40...etc....
        #it lists type of win at 19, 36, 53, ....etc...
        
        
        temp_count=0
        dec_maj_count = 0
        dec_split_count = 0
        dec_un_count = 0
        ko_count = 0
        sub_count = 0
        win_flag = False #Set to true when we have a win

        
        
        
        for row_temp in blue_rounds_raw:
            cols_method = row_temp.find_all('p', {'class': 'b-fight-details__table-text'})
            if len(cols_method) > 16:
                pos_date = (cols_method[12].get_text().strip())
                event_date_parsed = parse(formatted_date)
                fight_date_parsed = parse(pos_date)
                if fight_date_parsed < event_date_parsed:


                    b = (cols_method[13])
                    pos_flag = (cols_method[0].get_text().strip())
                    if(pos_flag) == 'win':
                        win_flag = True
                    else:
                        win_flag = False
                #Now we are going to look at the win_flag.  If it's
                #true we can tally the method
                    if (win_flag == True):
                        if(b.get_text().strip())=='M-DEC':
                            dec_maj_count += 1
                        elif(b.get_text().strip())=='S-DEC':
                            dec_split_count +=1
                        elif(b.get_text().strip())=='U-DEC':
                            dec_un_count += 1
                        elif(b.get_text().strip())=='KO/TKO':
                            ko_count += 1
                        elif(b.get_text().strip())=='SUB':
                            sub_count += 1
                        
            temp_count+=1
        
        blue_total_maj_dec.append(dec_maj_count)
        blue_total_split_dec.append(dec_split_count)    
        blue_total_un_dec.append(dec_un_count)
        blue_total_ko.append(ko_count)
        blue_total_sub.append(sub_count)
                #if (temp_count - 4) % 17 == 0:
        #            #print(b.get_text().strip())
        #            round_raw = b.get_text()
        #            round_stripped = round_raw.strip()
        #            round_count+=int(round_stripped)
        #            #print(round_count)
        #    temp_count+=1
        #blue_total_rounds.append(round_count)
        ################################################################












        win_streak = 0
        lose_streak =0
        draw_count=0
        end_streak = False #Set to true when the streak is over
        #print(dates_list)
        longest_win_streak = 0
        temp_win_streak = 0
        total_losses=0
        total_wins=0
        for r in blue_results_raw:
            r=r.get_text()
            if r != 'next':
                d = dates_list.pop(0)
                event_date_parsed = parse(formatted_date)
                fight_date_parsed = parse(d)
                if fight_date_parsed < event_date_parsed:
                    #print(f"{fight_date_parsed} is earlier than {event_date_parsed}")                
                    #print(r)
                    if r=='draw':
                        draw_count+=1        
                    if end_streak == False:
                        if r=='next': #Usually the first line.  Just skip
                            pass
                        elif r=='win':
                            if (win_streak>0):
                                win_streak+=1
                            elif(win_streak==0 and lose_streak==0):
                                win_streak+=1
                            else:
                                end_streak = True
                        elif r=='loss':
                            if (lose_streak>0):
                                lose_streak+=1
                            elif(win_streak==0 and lose_streak==0):
                                lose_streak+=1
                            else:
                                end_streak=True
                    b = r
                    if b=='draw':
                        if temp_win_streak > longest_win_streak:
                            longest_win_streak = temp_win_streak
                        temp_win_streak = 0
                    if b=='win':
                        temp_win_streak += 1
                        total_wins+=1
                    elif b=='loss':
                        temp_win_streak = 0
                        total_losses+=1
                    if temp_win_streak > longest_win_streak:
                        longest_win_streak = temp_win_streak

                        
            #print(r)
        #print(f"Win Streak: {win_streak}. Lose streak: {lose_streak}")
        blue_fighter_win_streak.append(win_streak)
        blue_fighter_lose_streak.append(lose_streak)
        blue_draw_list.append(draw_count)
        blue_fighter_longest_win_streak.append(longest_win_streak)
        blue_total_losses.append(total_losses)
        blue_total_wins.append(total_wins)
        if did_red_lose_list[z]:
            r_fighter_file=open(os.path.join(current_script_dir, f'fighter_pages/b{z}.html'), "r")
        else:
            r_fighter_file=open(os.path.join(current_script_dir, f'fighter_pages/r{z}.html'), "r")
            
        red_soup=BeautifulSoup(r_fighter_file.read(), 'html.parser')
        red_results_raw = red_soup.find_all('i',{'class':'b-flag__text'})
        red_rounds_raw = red_soup.find_all('p', {'class':'b-fight-details__table-text'})
    
        ################################################################
        #Red Total rounds fought
        #Round totals are on 21, 38, 55, 72... etc...
        #So that is (count - 4) % 17 = 0
        
        red_rounds_raw = red_soup.find_all('tr', {'class':'b-fight-details__table-row'})
        #print(f"Fight rows: {len(blue_fight_dates_raw)}")
        red_round_count = 0
        for row_temp in red_rounds_raw:
            pos_dates = row_temp.find_all('p', {'class': 'b-fight-details__table-text'})
            if len(pos_dates) > 16:
                pos_date = (pos_dates[12].get_text().strip())
                event_date_parsed = parse(formatted_date)
                fight_date_parsed = parse(pos_date)
                if fight_date_parsed < event_date_parsed:
                    red_round_count = red_round_count + int(pos_dates[15].get_text().strip())

        
        red_total_rounds.append(red_round_count)
        ################################################################

        red_fight_dates_raw = red_soup.find_all('tr', {'class':'b-fight-details__table-row'})
        #print(f"Fight rows: {len(red_fight_dates_raw)}")
        for row_temp in red_fight_dates_raw:
            pos_dates = row_temp.find_all('p', {'class': 'b-fight-details__table-text'})
            if len(pos_dates) > 16:
                dates_list_red.append(pos_dates[12].get_text().strip())

        
        
        ###############################################################
        #Red total title bouts.  We are looking for 'belt.png'
        title_bout_count = 0
        
        #print(blue_soup)
        title_bout_count = str(red_soup).count('belt.png')
        #print(title_bout_count)
        #If the upcoming fight is a title bout we need to subtract 1
        if(df.iloc[z]['TitleBout']):
            title_bout_count -= 1
        red_title_bouts.append(title_bout_count)    
        
        ###############################################################




        ################################################################
        #Determine the type of win for BLUE
        temp_count = 0
        #OK so it lists win or loss at 6, 23, 40...etc....
        #it lists type of win at 19, 36, 53, ....etc...
        
        
        temp_count=0
        dec_maj_count = 0
        dec_split_count = 0
        dec_un_count = 0
        ko_count = 0
        sub_count = 0
        win_flag = False #Set to true when we have a win

        
        
        
        
        
        for row_temp in red_rounds_raw:
            cols_method = row_temp.find_all('p', {'class': 'b-fight-details__table-text'})
            if len(cols_method) > 16:
                pos_date = (cols_method[12].get_text().strip())
                event_date_parsed = parse(formatted_date)
                fight_date_parsed = parse(pos_date)
                if fight_date_parsed < event_date_parsed:


                    b = (cols_method[13])
                    pos_flag = (cols_method[0].get_text().strip())
                    if(pos_flag) == 'win':
                        win_flag = True
                    else:
                        win_flag = False
                #Now we are going to look at the win_flag.  If it's
                #true we can tally the method
                    if (win_flag == True):
                        if(b.get_text().strip())=='M-DEC':
                            dec_maj_count += 1
                        elif(b.get_text().strip())=='S-DEC':
                            dec_split_count +=1
                        elif(b.get_text().strip())=='U-DEC':
                            dec_un_count += 1
                        elif(b.get_text().strip())=='KO/TKO':
                            ko_count += 1
                        elif(b.get_text().strip())=='SUB':
                            sub_count += 1
                        
            temp_count+=1
        
        red_total_maj_dec.append(dec_maj_count)
        red_total_split_dec.append(dec_split_count)    
        red_total_un_dec.append(dec_un_count)
        red_total_ko.append(ko_count)
        red_total_sub.append(sub_count)






        win_streak = 0
        lose_streak =0
        draw_count=0
        longest_win_streak = 0
        temp_win_streak = 0
        total_losses = 0 
        total_wins = 0
        end_streak = False #Set to true when the streak is over
        for r in red_results_raw:
            r=r.get_text()
            if r != 'next':
                d = dates_list_red.pop(0)
                event_date_parsed = parse(formatted_date)
                fight_date_parsed = parse(d)
                if fight_date_parsed < event_date_parsed:
                    if r=='draw':
                        draw_count+=1        
                    if end_streak == False:
                        if r=='next': #Usually the first line.  Just skip
                            pass
                        elif r=='win':
                            if (win_streak>0):
                                win_streak+=1
                            elif(win_streak==0 and lose_streak==0):
                                win_streak+=1
                            else:
                                end_streak = True
                        elif r=='loss':
                            if (lose_streak>0):
                                lose_streak+=1
                            elif(win_streak==0 and lose_streak==0):
                                lose_streak+=1
                            else:
                                end_streak=True
                    b = r
                    if b=='draw':
                        if temp_win_streak > longest_win_streak:
                            longest_win_streak = temp_win_streak
                        temp_win_streak = 0
                    if b=='win':
                        temp_win_streak += 1
                        total_wins+=1
                    elif b=='loss':
                        temp_win_streak = 0
                        total_losses+=1
                    if temp_win_streak > longest_win_streak:
                        longest_win_streak = temp_win_streak
                        
            #print(r)
        #print(f"Win Streak: {win_streak}. Lose streak: {lose_streak}")
        red_fighter_win_streak.append(win_streak)
        red_fighter_lose_streak.append(lose_streak)
        red_draw_list.append(draw_count)
        red_fighter_longest_win_streak.append(longest_win_streak)
        red_total_losses.append(total_losses)
        red_total_wins.append(total_wins)
        
        ###################################################################
        #onto some data we do not need to calculate
        #Sig Strikes Landed: {SLpM}
        #Sig Strikes Percent {Str. Acc}
        blue_strikes_raw = blue_soup.find_all('li',
                                {'class':'b-list__box-list-item b-list__box-list-item_type_block'})

        red_strikes_raw = red_soup.find_all('li',
                                {'class':'b-list__box-list-item b-list__box-list-item_type_block'})
        
        #print()
        #print()
        #print()
        s_count = 0
        for s in blue_strikes_raw:
            if s_count == 5:
                blue_strikes = str(s)
                blue_strikes = blue_strikes.split('</i>')
                blue_strikes = blue_strikes[1]
                #print(temp)
                #There is a tag at the end we need to strip
                blue_strikes = blue_strikes[:-5]
                blue_strikes=blue_strikes.strip()
                #print(blue_strikes.strip())
                blue_strike_list.append(blue_strikes)
                #print(s)   
            if s_count == 6:
                blue_str_acc = str(s)
                blue_str_acc = blue_str_acc.split('</i>')
                blue_str_acc = blue_str_acc[1]
                #print(temp)
                #There is a tag at the end we need to strip
                blue_str_acc = blue_str_acc[:-5]
                blue_str_acc=blue_str_acc.strip()
                #print(blue_strikes.strip())
                blue_strike_acc_list.append('.'+blue_str_acc[:-1])
                #print(s)   
            else:
                #I think we can get the value without caring too
                #much what it is..... This should save some coding
                isolate_stat = str(s)
                isolate_stat = isolate_stat.split('</i>')
                isolate_stat = isolate_stat[1]
                isolate_stat = isolate_stat[:-5]
                isolate_stat = isolate_stat.strip()
                if s_count == 13:
                    sub_list.append(isolate_stat)
                if s_count == 10:
                    td_list.append(isolate_stat)
                if s_count == 11:   #td_accuracy
                    #We need to remove the percent sign
                    isolate_stat = isolate_stat[:-1]
                    #We need to convert to decimal
                    isolate_stat = float(isolate_stat) / 100
                    td_acc_list.append(isolate_stat)
                if s_count ==3:
                    #Stance
                    stance_list.append(isolate_stat)
                if s_count == 0:
                    #Height
                    #print(isolate_stat)
                    #We need to split into feet and inches and
                    #convert to cm....
                    isolate_stat = isolate_stat.replace("'", "")
                    isolate_stat = isolate_stat.replace('"', '')
                    height_tuple = isolate_stat.split(" ")
                    if isolate_stat == ('--'):
                        total_inches = 0
                    else:
                        total_inches = int(height_tuple[0])*12 + int(height_tuple[1])
                    height_in_cm = total_inches * 2.54
                    #print(height_tuple)
                    #print(total_inches)
                    #print(height_in_cm)
                    height_list.append(height_in_cm)
                if s_count == 2:
                    #Reach
                    isolate_stat = isolate_stat.replace('"', '')
                    if isolate_stat == ('--'):
                        reach_in_cm = height_in_cm
                    else:
                        reach_in_cm = int(isolate_stat) * 2.54

                    reach_list.append(reach_in_cm)
                if s_count == 1:
                    #weight
                    #print(isolate_stat)
                    isolate_stat = isolate_stat.replace(" lbs.", '')
                    #print(isolate_stat)
                    weight_list.append(isolate_stat)
                if s_count == 4:
                    #Age
                    #print(isolate_stat)
                    #print(formatted_date)
                    if isolate_stat == '--':
                        age = 30
                    else:
                        birth_date = datetime.strptime(isolate_stat, "%b %d, %Y")
                        age = date_datetime.year - birth_date.year - ((date_datetime.month, date_datetime.day) < (birth_date.month, birth_date.day))
                    
                    blue_age_list.append(age)
            #print(s_count)
            #print(s)
            s_count+=1
        #print()
        #print()
        #print()



        s_count = 0
        for s in red_strikes_raw:
            if s_count == 5:
                red_strikes = str(s)
                red_strikes = red_strikes.split('</i>')
                red_strikes = red_strikes[1]
                #print(temp)
                #There is a tag at the end we need to strip
                red_strikes = red_strikes[:-5]
                red_strikes=red_strikes.strip()
                #print(blue_strikes.strip())
                red_strike_list.append(red_strikes)
                #print(len(red_strike_list))
            if s_count == 6:
                red_str_acc = str(s)
                red_str_acc = red_str_acc.split('</i>')
                red_str_acc = red_str_acc[1]
                #print(temp)
                #There is a tag at the end we need to strip
                red_str_acc = red_str_acc[:-5]
                red_str_acc=red_str_acc.strip()
                #print(blue_strikes.strip())
                red_strike_acc_list.append('.'+red_str_acc[:-1])
                #print(s)   
            else:
                #I think we can get the value without caring too
                #much what it is..... This should save some coding
                isolate_stat = str(s)
                isolate_stat = isolate_stat.split('</i>')
                isolate_stat = isolate_stat[1]
                isolate_stat = isolate_stat[:-5]
                isolate_stat = isolate_stat.strip()
                if s_count == 13:
                    red_sub_list.append(isolate_stat)
                if s_count == 10:
                    red_td_list.append(isolate_stat)
                if s_count == 11:   #td_accuracy
                    #We need to remove the percent sign
                    isolate_stat = isolate_stat[:-1]
                    #We need to convert to decimal
                    isolate_stat = float(isolate_stat) / 100
                    red_td_acc_list.append(isolate_stat)
                if s_count ==3:
                    #Stance
                    red_stance_list.append(isolate_stat)
                if s_count == 0:
                    #Height
                    #print(isolate_stat)
                    #We need to split into feet and inches and
                    #convert to cm....
                    isolate_stat = isolate_stat.replace("'", "")
                    isolate_stat = isolate_stat.replace('"', '')
                    height_tuple = isolate_stat.split(" ")
                    total_inches = int(height_tuple[0])*12 + int(height_tuple[1])
                    height_in_cm = total_inches * 2.54
                    #print(height_tuple)
                    #print(total_inches)
                    #print(height_in_cm)
                    red_height_list.append(height_in_cm)
                if s_count == 2:
                    #Reach
                    isolate_stat = isolate_stat.replace('"', '')
                    if isolate_stat == '--':
                        reach_in_cm = height_in_cm
                    else:
                        reach_in_cm = int(isolate_stat) * 2.54
                    red_reach_list.append(reach_in_cm)
                if s_count == 1:
                    #weight
                    #print(isolate_stat)
                    isolate_stat = isolate_stat.replace(" lbs.", '')
                    #print(isolate_stat)
                    red_weight_list.append(isolate_stat)
                if s_count == 4:
                    #Age
                    if isolate_stat == '--':
                        age = 30
                    else:
                        birth_date = datetime.strptime(isolate_stat, "%b %d, %Y")
                        age = date_datetime.year - birth_date.year - ((date_datetime.month, date_datetime.day) < (birth_date.month, birth_date.day))
                    red_age_list.append(age)


            s_count+=1





    #THESE MIGHT BE FLIPPED!


    #Here we add all the lists to the dataframe    

    if (is_most_recent):
        df['Finish'] =  finish_list
        df['FinishDetails'] = finish_details_list
        df['FinishRound'] = finish_round_list
        df['FinishRoundTime'] = time_list
        
        def get_fight_time_secs(r, t):
            r = int(r)
            if r== '' or t == '':
                return ''
            else:
                calculated_time = 300 * (r-1)
                t_split = str(t).split(':')
                #Check for nan
                if t_split[0] != 'nan':
                    calculated_time = calculated_time + 60 * int(t_split[0]) + int(t_split[1])
            return calculated_time    

        df['TotalFightTimeSecs'] = df.apply(lambda x: get_fight_time_secs(x['FinishRound'], x['FinishRoundTime']), axis=1)
        
    df['Winner'] = winner_list
    df['BlueCurrentWinStreak'] = blue_fighter_win_streak
    df['BlueCurrentLoseStreak'] = blue_fighter_lose_streak
    df['RedCurrentWinStreak'] = red_fighter_win_streak
    df['RedCurrentLoseStreak'] = red_fighter_lose_streak
    df['RedLongestWinStreak'] = red_fighter_longest_win_streak
    df['BlueLongestWinStreak'] = blue_fighter_longest_win_streak
    df['BlueLosses'] = blue_total_losses
    df['RedLosses'] = red_total_losses
    df['BlueTotalRoundsFought'] = blue_total_rounds
    df['RedTotalRoundsFought'] = red_total_rounds
    df['BlueTotalTitleBouts'] = blue_title_bouts
    df['RedTotalTitleBouts'] = red_title_bouts
    df['BlueWinsByDecisionMajority'] = blue_total_maj_dec
    df['BlueWinsByDecisionSplit'] = blue_total_split_dec
    df['BlueWinsByDecisionUnanimous'] = blue_total_un_dec
    df['BlueWinsByKO'] = blue_total_ko
    df['BlueWinsBySubmission'] = blue_total_sub
    df['BlueWinsByTKODoctorStoppage'] = 0
    df['BlueWins'] = blue_total_wins
    df['RedWins'] = red_total_wins
    df['RedWinsByDecisionMajority'] = red_total_maj_dec
    df['RedWinsByDecisionSplit'] = red_total_split_dec
    df['RedWinsByDecisionUnanimous'] = red_total_un_dec
    df['RedWinsByKO'] = red_total_ko
    df['RedWinsBySubmission'] = red_total_sub
    df['RedWinsByTKODoctorStoppage'] = 0

    df['BlueReachCms'] = reach_list
    df['BlueWeightLbs'] = weight_list
    df['RedReachCms'] = red_reach_list
    df['RedWeightLbs'] = red_weight_list

    #Draws
    df['RedDraws'] = red_draw_list
    df['BlueDraws'] = blue_draw_list
    df['BlueAvgSigStrLanded'] = blue_strike_list
    df['RedAvgSigStrLanded'] = red_strike_list
    df['BlueAvgSigStrPct'] = blue_strike_acc_list
    df['RedAvgSigStrPct'] = red_strike_acc_list
    df['BlueAvgSubAtt'] = sub_list
    df['BlueAvgTDLanded'] = td_list
    df['RedAvgSubAtt'] = red_sub_list
    df['RedAvgTDLanded'] = red_td_list

    df['BlueAvgTDPct'] = td_acc_list
    df['RedAvgTDPct'] = red_td_acc_list

    df['BlueStance'] = stance_list
    df['BlueHeightCms'] = height_list
    df['RedStance'] = red_stance_list
    df['RedHeightCms'] = red_height_list

    df['BlueAge'] = blue_age_list
    df['RedAge'] = red_age_list

    #Differences!!!
    df['WinStreakDif'] = df['BlueCurrentWinStreak'] - df['RedCurrentWinStreak']
    df['LoseStreakDif'] = df['BlueCurrentLoseStreak'] - df['RedCurrentLoseStreak']
    df['LongestWinStreakDif'] = df['BlueLongestWinStreak'] - df['RedLongestWinStreak']
    df['WinDif'] = df['BlueWins'] - df['RedWins']
    df['LossDif'] = df['BlueLosses'] - df['RedLosses']
    df['TotalRoundDif'] = df['BlueTotalRoundsFought'] - df['RedTotalRoundsFought']
    df['TotalTitleBoutDif'] = df['BlueTotalTitleBouts'] - df['RedTotalTitleBouts']
    df['KODif'] = df['BlueWinsByKO'] - df['RedWinsByKO']
    df['SubDif'] = df['BlueWinsBySubmission'] - df['RedWinsBySubmission']
    df['HeightDif'] = df['BlueHeightCms'] - df['RedHeightCms']
    df['ReachDif'] = df['BlueReachCms'] - df['RedReachCms']
    df['SigStrDif'] = df['BlueAvgSigStrLanded'].astype(float) - df['RedAvgSigStrLanded'].astype(float)
    df['AvgSubAttDif'] = df['BlueAvgSubAtt'].astype(float) - df['RedAvgSubAtt'].astype(float)
    df['AvgTDDif'] = df['BlueAvgTDLanded'].astype(float) - df['RedAvgTDLanded'].astype(float)
    df['EmptyArena'] = 1
    df['AgeDif'] = df['BlueAge'] - df['RedAge']

    red_count = 0
    for f in red_fighter_list:
        #print(f[1][7:])
        
        html= urlopen(f[1])
        bs = BeautifulSoup(html.read(), 'html.parser')
        with open(os.path.join(current_script_dir, f'fighter_pages/r{red_count}.html'), "w", encoding='utf-8') as file:
            file.write("")
    

        red_count+=1

    blue_count = 0
    for f in blue_fighter_list:
        #print(f[1][7:])
        
        html= urlopen(f[1])
        bs = BeautifulSoup(html.read(), 'html.parser')
        with open(os.path.join(current_script_dir, f'fighter_pages/b{blue_count}.html'), "w", encoding='utf-8') as file:
            file.write("")
    

        blue_count+=1

    master = pd.read_csv(ufc_master_relative_path)
    master_df = pd.concat([df, master], ignore_index=True)
    master_df.to_csv(ufc_master_relative_path, index=False)

    df.to_csv(os.path.join(current_script_dir, "scraped_event.csv"), index=False)
    print("Data Scraped and Saved")


def clean_up_data():
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(current_script_dir, "scraped_event.csv"))
    df = data_cleaning.clean_up_data(df)
    df = data_cleaning.get_elos_and_streaks(df)
    df = data_cleaning.get_defense_data(df)
    df = data_cleaning.calculate_metrics(df)
    df = data_cleaning.get_data_points(df)
    df = data_cleaning.extract_fighter_stats(df)
    df.to_csv(os.path.join(current_script_dir, "fighter_stats.csv"), index=False)
    print("Data Cleaned and Saved")
    return df

def update_db():
    db = firestore.Client(project="ufc-proj", database="ufcdb")
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    stats_relative_path = os.path.join(current_script_dir, "fighter_stats.csv")
    df = pd.read_csv(stats_relative_path)

    records = df.to_dict(orient="records")

    for i in range(len(records)):
        record = records[i]
        doc_id = str(record.get('Fighter')) 
        doc_ref = db.collection("fighters").document(doc_id)
        doc_ref.set(record, merge=True)

if __name__ == "__main__":
    scrape_previous_fights()
    clean_up_data()
    update_db()