from ._FUNCS_ import *
from .WELLAPI import *
from .DATA import *
from .SURVEYS import *
from .MAP import convert_XY

__all__ = ['CONSTRUCT_DB',
          'UPDATE_SURVEYS']

def CONSTRUCT_DB(DB_NAME = 'FIELD_DATA.db'):
    pathname = path.dirname(argv[0])
    adir = path.abspath(pathname)
    
    connection_obj = sqlite3.connect(DB_NAME)
    c = connection_obj.cursor()
    SURVEY_FILE_FIELDS = {'FILENAME':['CHAR'],'FILE':['BLOB']}
    INIT_SQL_TABLE(connection_obj, 'SURVEYFILES', SURVEY_FILE_FIELDS)
    
    c.execute(''' SELECT DISTINCT FILENAME FROM SURVEYFILES  ''')
    LOADED_FILES = c.fetchall()
    LOADED_FILES = list(set(itertools.chain(*LOADED_FILES)))
    
    SURVEYFOLDER = 'SURVEYFOLDER'
    XLSLIST = filelist(SURVEYFOLDER,None,None,'.xls')
    USELIST = list(set(XLSLIST).difference(set(LOADED_FILES)))

    print('{} FILES TO LOAD'.format(len(USELIST)))

    for F in USELIST:
        if '~' in F:
            continue
        B = convertToBinaryData(path.join(SURVEYFOLDER,F))
        
        SQL_QRY = ''' INSERT INTO SURVEYFILES(FILENAME, FILE) VALUES (?,?)'''
        data_tuple = (F,B)

        load_surveyfile(connection_obj,data_tuple)
        
    connection_obj.commit()

    #DATA = READ_SQL_TABLE(connection_obj,'SURVEYFILES')
    #DATA_df = pd.DataFrame(DATA, columns = ['FILE','BLOB'])
    DATA_df = pd.read_sql('SELECT * FROM SURVEYFILES', connection_obj)

    DATA_COLS = {'MD': 'REAL',
             'INC': 'REAL', 
             'AZI':'REAL',
             'TVD':'REAL',
             'NORTH_dY':'REAL',
             'EAST_dX':'REAL',
             'UWI':'INTEGER',
             'FILE': 'TEXT'
             }
    
 
    INIT_SQL_TABLE(connection_obj,'SURVEYDATA', DATA_COLS)

    QRY = 'SELECT DISTINCT UPPER(FILE) FROM SURVEYDATA'
    c.execute(QRY)
    SCANNEDFILES = c.fetchall()
    SCANNEDFILES = list(itertools.chain(*SCANNEDFILES))
    m = DATA_df.loc[~DATA_df.FILENAME.str.upper().isin(SCANNEDFILES)].index

    S_KEYS = pd.read_sql('SELECT * FROM SURVEYDATA LIMIT 1', connection_obj).keys()
    OUT = pd.DataFrame(columns = S_KEYS)

    warnings.filterwarnings('ignore')

    batch = min(5000,len(m))
    chunksize = max(int(len(m)/batch),1)
    mm=np.array_split(m,chunksize)

    for m1 in mm:
        OUT = pd.DataFrame(columns = S_KEYS)
        for D in DATA_df.loc[m1].values:
            if 'LOCK.' in D[0].upper():
                continue

            FILE = D[0]
    
            if D[0].upper() in SCANNEDFILES:
                continue

            try:
                dd = survey_from_excel(tuple(D),ERRORS = False)
            except Exception as e:
                print(f'EXCEPTION:{FILE} :: {e}')
            if isinstance(dd,pd.DataFrame):
                dd['FILE'] = FILE
                OUT = pd.concat([OUT,dd])
                
        if not OUT.empty:
            #OUT.rename(columns = {'UWI10':'UWI'}, inplace =True)
            #OUT['UWI10'] = OUT.UWI.apply(lambda x: WELLAPI(x).API2INT(10))
            OUT.to_sql('SURVEYDATA',index = False, con = connection_obj, if_exists = 'append', chunksize = 5000)
         
    SQL_UNDUPLICATE(connection_obj,'SURVEYDATA')
    
    warnings.filterwarnings('default')

    ALL_SURVEYS = pd.read_sql_query('SELECT * FROM SURVEYDATA',connection_obj)
    ALL_SURVEYS['UWI10'] = ALL_SURVEYS.UWI.apply(lambda x:WELLAPI(x).API2INT(10))
    
    #ddf = CO_ABS_LOC(ALL_SURVEYS.UWI10,'CO_3_2.1.sqlite')
    
    # DROP OR FIX UWIS IN CO_ABS_LOC, NOT USED CURRENTLY
    #ALL_SURVEYS = pd.merge(ALL_SURVEYS, ddf,how = 'left',on='UWI10',left_index = False, right_index = False)
    #ALL_SURVEYS['X_PATH'] = ALL_SURVEYS[['EAST_dX',AL'X_FEET']].sum(axis=1)
    #ALL_SURVEYS['Y_PATH'] = ALL_SURVEYS[['NORTH_dY','Y_FEET']].sum(axis=1)
    
    # OLD PREFERRED SURVEYS
    QRY = 'SELECT FILE, UWI10, FAVORED_SURVEY FROM FAVORED_SURVEYS' # WHERE FAVORED_SURVEY = 1'
    OLD_PREF = pd.read_sql(QRY, connection_obj)

    #m = ALL_SURVEYS[['UWI10','FILE']].drop_duplicates().apply(tuple,1).isin(OLD_PREF[['UWI10','FILE']].apply(tuple,1))
    m = ALL_SURVEYS[['UWI10','FILE']].merge(OLD_PREF[['UWI10','FILE']],indicator = True, how='left').loc[lambda x : x['_merge']!='both'].index

    #assign favored file definitions from old table
    ALL_SURVEYS['FAVORED_SURVEY'] = -1
    ALL_SURVEYS.loc[~ALL_SURVEYS.index.isin(m),'FAVORED_SURVEY'] = ALL_SURVEYS.loc[~ALL_SURVEYS.index.isin(m),['UWI10','FILE']].merge(OLD_PREF,on=['UWI10','FILE'])['FAVORED_SURVEY']

    #UWIs with new file
    NEW_UWI = ALL_SURVEYS.loc[m,'UWI10'].unique().tolist()
    m = ALL_SURVEYS.loc[ALL_SURVEYS.UWI10.isin(NEW_UWI)].index  

    if len(m)>0:
        #CONDENSE_DICT = SURVEYS.Condense_Surveys(ALL_SURVEYS[['UWI10','FILE','MD', 'INC', 'AZI', 'TVD','X_PATH', 'Y_PATH']])
        # CONDENSE_DICT = SURVEYS.Condense_Surveys(ALL_SURVEYS.loc[m])
        CONDENSE_DICT = SURVEYS.Condense_Surveys(ALL_SURVEYS.loc[m,['UWI10','FILE','MD', 'INC', 'AZI', 'TVD','NORTH', 'EAST']])
        ALL_SURVEYS.loc[m,'FAVORED_SURVEY'] = ALL_SURVEYS.loc[m,'UWI10'].apply(lambda x:CONDENSE_DICT[x])
    
    #m = FAVORED_SURVEY.apply(lambda x:CONDENSE_DICT[x.UWI10] == x.FILE, axis=1)
    m = (ALL_SURVEYS.FAVORED_SURVEY == 1)
    USE_SURVEYS = ALL_SURVEYS.loc[m]
    USE_SURVEYS['UWI10'] = USE_SURVEYS.UWI.apply(lambda x:WELLAPI(x).API2INT(10))

    # CREATE ABSOLUTE LOCATION TABLE if True:
    WELL_LOC = read_shapefile(shp.Reader('Wells.shp'))
    
    WELL_LOC['UWI10'] = WELL_LOC.API.apply(lambda x:WELLAPI('05'+str(x)).API2INT(10))
    WELL_LOC = WELL_LOC.loc[~(WELL_LOC['UWI10'] == 500000000)]
    WELL_LOC['X'] = WELL_LOC.coords.apply(lambda x:x[0][0])
    WELL_LOC['Y'] = WELL_LOC.coords.apply(lambda x:x[0][1])

    WELLPLAN_LOC = read_shapefile(shp.Reader('Directional_Lines_Pending.shp'))
    WELLPLAN_LOC['UWI10'] = WELLPLAN_LOC.API.apply(lambda x:WELLAPI('05'+str(x)).API2INT(10))
    WELLPLAN_LOC = WELLPLAN_LOC.loc[~(WELLPLAN_LOC['UWI10'] == 500000000)]
    WELLPLAN_LOC['X'] = WELLPLAN_LOC.coords.apply(lambda x:x[0][0])
    WELLPLAN_LOC['Y'] = WELLPLAN_LOC.coords.apply(lambda x:x[0][1])
    
    WELLLINE_LOC = read_shapefile(shp.Reader('Directional_Lines.shp'))
    WELLLINE_LOC['UWI10'] = WELLLINE_LOC.API.apply(lambda x:WELLAPI('05'+str(x)).API2INT(10))
    WELLLINE_LOC = WELLLINE_LOC.loc[~(WELLLINE_LOC['UWI10'] == 500000000)]
    WELLLINE_LOC['X'] = WELLLINE_LOC.coords.apply(lambda x:x[0][0])
    WELLLINE_LOC['Y'] = WELLLINE_LOC.coords.apply(lambda x:x[0][1])
    
    LOC_COLS = ['UWI10','X','Y']
    LOC_DF = WELLLINE_LOC[LOC_COLS].drop_duplicates()
    m = WELLPLAN_LOC.index[~(WELLPLAN_LOC.UWI10.isin(LOC_DF.UWI10))]
    LOC_DF = pd.concat([LOC_DF,WELLPLAN_LOC.loc[m,LOC_COLS].drop_duplicates()])
    m = WELL_LOC.index[~(WELL_LOC.UWI10.isin(LOC_DF.UWI10))]
    LOC_DF = pd.concat([LOC_DF,WELL_LOC.loc[m,LOC_COLS].drop_duplicates()])
    LOC_DF.UWI10.shape[0]-len(LOC_DF.UWI10.unique())
    
    LOC_DF[['XFEET','YFEET']] = pd.DataFrame(convert_XY(LOC_DF.X,LOC_DF.Y,26913,2231)).T.values

    LOC_COLS = {'UWI10': 'INTEGER',
                'X': 'REAL',
                'Y': 'REAL',
                'XFEET':'REAL',
                'YFEET':'REAL'}
    INIT_SQL_TABLE(connection_obj, 'SHL', LOC_COLS)
    LOC_DF.to_sql(name = 'SHL', con = connection_obj, if_exists='replace', index = False, dtype = LOC_COLS)
    connection_obj.commit()
    
    #FLAG PREFERRED SURVEYS if True:
    ALL_SURVEYS['UWI10'] = ALL_SURVEYS.UWI.apply(lambda x:WELLAPI(x).API2INT(10))
    ALL_SURVEYS = ALL_SURVEYS.merge(LOC_DF[['UWI10','XFEET','YFEET']],how = 'left', on = 'UWI10')
    ALL_SURVEYS['NORTH'] = ALL_SURVEYS[['NORTH_dY','YFEET']].sum(axis=1)
    ALL_SURVEYS['EAST'] = ALL_SURVEYS[['EAST_dX','XFEET']].sum(axis=1)
    ALL_SURVEYS.rename({'YFEET':'SHL_Y_FEET','XFEET':'SHL_X_FEET'}, axis = 1, inplace = True)

   
    #ALL_SURVEYS['FAVORED_SURVEY'] = ALL_SURVEYS.apply(lambda x: CONDENSE_DICT[x.UWI10], axis = 1).str.upper() == ALL_SURVEYS.FILE.str.upper()

    SCHEMA = {'UWI10': 'INTEGER', 'FILE':'TEXT', 'FAVORED_SURVEYS':'INTEGER'}
    #INIT_SQL_TABLE(connection_obj,'SURVEYDATA', SCHEMA)

    m = ALL_SURVEYS.FAVORED_SURVEY==1
    ALL_SURVEYS.loc[:,['UWI10','FILE','FAVORED_SURVEY']].drop_duplicates().to_sql('FAVORED_SURVEYS',
                                                   connection_obj,
                                                   schema = SCHEMA,
                                                   if_exists = 'replace')
    
    connection_obj.commit()

    # XYZ SPACING CALC
    # PARENT CUM AT TIME OF CHILD FRAC
    # PAD ASSIGNMENTS FROM SPACING GROUPS (SAME SHL)
    # UNIT ASSIGNMENTS: NEAREST IN DATE DIFF RANGE AND EITHER LATERAL IS 90% OVERLAPPING OTHER

    QRY = 'SELECT CAST(max(S.UWI10, P.UWI10) as INT) AS UWI10, S.FIRST_PRODUCTION_DATE, S.JOB_DATE, S.JOB_END_DATE, P.FIRST_PRODUCTION FROM SCOUTDATA AS S LEFT JOIN PRODUCTION_SUMMARY AS P ON S.UWI10 = P.UWI10'
    WELL_DF = pd.read_sql(QRY,connection_obj)
    WELL_DF=WELL_DF.dropna(how='all',axis = 0)
    WELL_DF = WELL_DF.loc[~WELL_DF.UWI10.isna()]
    WELL_DF = DF_UNSTRING(WELL_DF)
    WELL_DF.sort_values(by = 'FIRST_PRODUCTION_DATE',ascending = False, inplace = True)


    UWIlist = WELL_DF.sort_values(by = 'UWI10', ascending = False).UWI10.tolist()
    processors = max(1,floor(multiprocessing.cpu_count()/1))
        
    chunksize = int(len(UWIlist)/processors)
    chunksize = 1000
    batch = int(len(UWIlist)/chunksize)
    #processors = max(processors,batch)
    data=np.array_split(UWIlist,batch)
    #print (f'batch = {batch}')
    func = partial(XYZSpacing,
            xxdf= ALL_SURVEYS.loc[m,['UWI10','FILE','MD', 'INC', 'AZI', 'TVD','NORTH', 'EAST']],
            df_UWI = WELL_DF,
            DATELIMIT = 360,
            SAVE = False)

    with concurrent.futures.ThreadPoolExecutor(max_workers = processors) as executor:
        f = {executor.submit(func,a): a for a in data}
    
    XYZ = pd.DataFrame()
    for i in f.keys():
        XYZ = XYZ.append(i.result(), ignore_index = True)

    XYZ = DF_UNSTRING(XYZ)    
    XYZ_COLS = FRAME_TO_SQL_TYPES(XYZ)
    
    XYZ.to_sql(name = 'SPACING', con = connection_obj, if_exists='replace', index = False, dtype = XYZ_COLS)
    connection_obj.commit()
          
    ###################
    # PRODUCTION DATA #
    ###################

    ##############
    # SCOUT DATA #
    ##############
    

    ###################
    # FRAC FOCUS DATA #
    ###################
    # CREATE FRAC FOCUS TABLE
    FF = DATA.Merge_Frac_Focus(DIR = 'FRAC_FOCUS', SAVE = False)
    FF = DF_UNSTRING(FF)
    FF_COLS = FRAME_TO_SQL_TYPES(FF)
    FF.to_sql(name = 'FRAC_FOCUS', con = connection_obj, if_exists = 'replace', index = False, dtype = FF_COLS)
    connection_obj.commit()    
    ###########################
    # ADD PROD VOLUMES TO XYZ #
    ###########################

    ###############################
    # DEVELOPMENT UNIT ASSIGNMENT #
    ###############################
    # TABLE OF UNIT/WELL
 
def UPDATE_SURVEYS():
    ###############
    # GET SURVEYS #
    ###############
    # Initialize constants
    global URL_BASE
    URL_BASE = 'https://cogcc.state.co.us/weblink/results.aspx?id=XNUMBERX'
    global DL_BASE 
    DL_BASE = 'https://cogcc.state.co.us/weblink/XLINKX'
    global pathname
    pathname = path.dirname(argv[0])
    global adir
    adir = path.abspath(pathname)
    global dir_add
    dir_add = path.abspath(path.dirname(argv[0]))+"\\SURVEYFOLDER"

    #Read UWI files and form UWI list
    WELL_LOC = read_shapefile(shp.Reader('Wells.shp'))
    WELLPLAN_LOC = read_shapefile(shp.Reader('Directional_Lines_Pending.shp'))
    WELLLINE_LOC = read_shapefile(shp.Reader('Directional_Lines.shp'))

    WELL_LOC['UWI10'] = WELL_LOC.API.apply(lambda x:WELLAPI('05'+str(x)).API2INT(10))
    WELLPLAN_LOC['UWI10'] = WELLPLAN_LOC.API.apply(lambda x:WELLAPI('05'+str(x)).API2INT(10))
    WELLLINE_LOC['UWI10'] = WELLLINE_LOC.API.apply(lambda x:WELLAPI('05'+str(x)).API2INT(10))

    SHP_UWIS = list(set(WELL_LOC['UWI10']).union(set(WELLPLAN_LOC['UWI10'])).union(set(WELL_LOC['UWI10'])))

    connection_obj = sqlite3.connect('FIELD_DATA.db')
    UWIPROD = pd.read_sql("SELECT DISTINCT UWI10 FROM PRODDATA WHERE First_of_Month LIKE '2022%'", connection_obj)
    UWIPROD = UWIPROD.UWI10.tolist()

    df = pd.read_sql('SELECT * FROM PRODUCTION_SUMMARY', connection_obj)
    connection_obj.close()
    
    df = DF_UNSTRING(df)
    OLD_UWI = df.loc[df.Month1.dt.year<2020, 'UWI10'].tolist()
    NEW_UWI = df.loc[df.Month1.dt.year>2020, 'UWI10'].tolist()
    
    FLIST = list()
    for file in listdir(dir_add):
        if file.lower().endswith(('.xls','xlsx','xlsm')):
            FLIST.append(file)

 
    SURVEYED_UWIS = [int(re.search(r'.*_UWI(\d*)\.',F).group(1)) for F in FLIST]
    UWIlist = list(set(OLD_UWI) - set(SURVEYED_UWIS))
    UWIlist.sort(reverse=True)
    
    #UWIlist = list(set(UWIPROD) - set(OLD_UWI))

    # Create download folder
    if not path.exists(dir_add):
            makedirs(dir_add)
    # Parallel Execution if 1==1:
    processors = min(1,floor(multiprocessing.cpu_count()/2))
        
    chunksize = int(len(UWIlist)/processors)
    chunksize = 1000
    batch = int(len(UWIlist)/chunksize)
    #processors = max(processors,batch)
    data=np.array_split(UWIlist,batch)
    #print (f'batch = {batch}')

    with concurrent.futures.ThreadPoolExecutor(max_workers = processors) as executor:
        f = {executor.submit(CO_Get_Surveys,a): a for a in data}
    
    
