import os
from dotenv import load_dotenv #pip install python-dotenv
import pandas as pd


load_dotenv("./.env")
INPUT_FILE = os.getenv("INPUT_FILE")
OUTPUT_GPRMC_FILE = os.getenv("OUTPUT_GPRMC_FILE")
OUTPUT_HEHDT_FILE = os.getenv("OUTPUT_HEHDT_FILE")

def main():
    print(INPUT_FILE)
    dataFrame = read_csv(INPUT_FILE)
    subFrame = process_df(dataFrame)
    export_dat(subFrame)
    return

def read_csv(path):
    df = pd.read_csv(path)
    #print(df)
    return df

def convert_to_spectre_format(lat, lon):
    # Convert Latitude to Spectre Format
    lat_deg = int(abs(lat))  # Extract degrees
    lat_min = (abs(lat) - lat_deg) * 60  # Convert fractional degrees to minutes
    lat_spectre = lat_deg * 100 + lat_min  # Combine degrees and minutes

    # Convert Longitude to Spectre Format
    lon_deg = int(abs(lon))  # Extract degrees
    lon_min = (abs(lon) - lon_deg) * 60  # Convert fractional degrees to minutes
    lon_spectre = lon_deg * 100 + lon_min  # Combine degrees and minutes

    return lat_spectre, lon_spectre

def process_df(df):
    subFrame = df.loc[:, ['timeStamp_ISO', 'lat[deg]', 'lon[deg]', 'easting[m]', 'northing[m]', 'Hdg[deg]', 'roll[deg]', 'pitch[deg]']]
    
    subFrame['NS'] = ['N'] * subFrame.shape[0]
    subFrame['EW'] = ['E'] * subFrame.shape[0]
    subFrame['GPRMC']  = ['GPRMC'] * subFrame.shape[0]
    subFrame['HEHDT'] = ['HEHDT'] * subFrame.shape[0]
    subFrame['PHTRO'] = ['PHTRO'] * subFrame.shape[0]
    
    # traverse the dataframe to modify the NS and EW columns
    for index, row in subFrame.iterrows():
        #print(row['easting[m]'])
        if row['lat[deg]'] < 0: # use north positive as reference 
            #subFrame.at[index, 'lat[deg]'] = -row['lat[deg]']
            subFrame.at[index, 'NS'] = 'S'

        if row['lon[deg]'] < 0: # use east positive as reference
            #subFrame.at[index, 'lon[deg]'] = -row['lon[deg]']
            subFrame.at[index, 'EW'] = 'W'

    # Apply the conversion function to each row and create new columns
    subFrame[['lat[spectre]', 'lon[spectre]']] = subFrame.apply(
        lambda row: convert_to_spectre_format(row['lat[deg]'], row['lon[deg]']),
        axis=1,
        result_type="expand"
    )

    #print(subFrame)
    return subFrame

def export_dat(df):
    # get columns
    timeStamp_Column = df['timeStamp_ISO']
    lat_Column = df['lat[spectre]']
    lon_Column = df['lon[spectre]']
    easting_Column = df['easting[m]']
    northing_Column = df['northing[m]']
    hdg_Column = df['Hdg[deg]']
    roll_Column = df['roll[deg]']
    pitch_Column = df['pitch[deg]']
    NS_Column = df['NS']
    EW_Column = df['EW']
    gprmc_Column = df['GPRMC']
    hehdt_Column = df['HEHDT']
    phtro_Column = df['PHTRO']

    # create GPRMC DF
    gprmcDF = pd.DataFrame({'timeStamp_ISO': timeStamp_Column, 'Msg': gprmc_Column, 'Easting': easting_Column, 'Northing': northing_Column, 'Lat[spectre]': lat_Column, 'NS': NS_Column, 'Lon[spectre]': lon_Column, 'EW': EW_Column})
    print(gprmcDF)

    gprmcDF.to_csv(OUTPUT_GPRMC_FILE, sep = ' ', index=False)

    # create HEHDT DF
    T_Column = ['T'] * len(hdg_Column)
    hehdtDF = pd.DataFrame({'timeStamp_ISO': timeStamp_Column, 'Msg': hehdt_Column, 'Heading': hdg_Column, 'T': T_Column})
    print(hehdtDF)

    # create PHTRO DF
    rollUnit_Column = ['P'] * len(roll_Column)
    pitchUnit_Column = ['T'] * len(pitch_Column)

    phtroDF = pd.DataFrame({'timeStamp_ISO': timeStamp_Column, 'Msg': phtro_Column, 'Pitch': pitch_Column, 'P_Unit': pitchUnit_Column, 'Roll': roll_Column, 'R_Unit': rollUnit_Column})

    # combine hehdtDF and phtroDF alternatively
    with open(OUTPUT_HEHDT_FILE, 'w') as f:
        # write the header
        f.write('timeStamp_ISO Msg\n')
        for index, row in hehdtDF.iterrows():
            f.write(f'{row["timeStamp_ISO"]} {row["Msg"]} {row["Heading"]}\n')

            if phtroDF['Roll'][index] < 0:
                phtroDF.at[index, 'Roll'] = -phtroDF['Roll'][index]
                phtroDF.at[index, 'R_Unit'] = 'B'
            if phtroDF['Pitch'][index] < 0:
                phtroDF.at[index, 'Pitch'] = -phtroDF['Pitch'][index]
                phtroDF.at[index, 'P_Unit'] = 'M'

            f.write(f'{row["timeStamp_ISO"]} {phtroDF["Msg"][index]} {phtroDF["Pitch"][index]} {phtroDF["P_Unit"][index]} {phtroDF["Roll"][index]} {phtroDF["R_Unit"][index]}\n')
    
    print(phtroDF)
    
    return

if __name__ == "__main__":
    main()