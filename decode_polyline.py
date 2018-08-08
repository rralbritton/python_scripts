def decode_polyline(polyline_str):
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    # Coordinates have variable length when encoded, so just keep
    # track of whether we've hit the end of the string. In each
    # while loop iteration, a single coordinate is decoded.
    while index < len(polyline_str):
        # Gather lat/lon changes, store them in a dictionary to apply them later
        for unit in ['latitude', 'longitude']: 
            shift, result = 0, 0

            while True:
                byte = ord(polyline_str[index]) - 63
                index+=1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break

            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']

        coordinates.append((lat / 100000.0, lng / 100000.0))

    print coordinates
    return coordinates

#RedLine    
decode_polyline('yyxwFdvsiTfA_AF_@Aa@_@eAa@gAmAjAqAdA_@DQ@_@Gq@g@qC@aDh@????eBX_Ex@kAPu@D??Q?O?yE???CgD?QAK?MCMAMEUCMCMEOEOSq@UYUUUQa@SYMcAYg@U_@_@QWQYOc@KEIa@Ga@Cu@?qA???aCDc@BWV{ADYZsB@GAG?GAEAC??Ha@BKFMHO~AaB??IKGIGEGAG?I?AH???@?BAB?BABEFEFKJ]\\ABIFEDEBIDGFML??IQM]IYGSG]B_ALq@Ha@B[?UE_@?S@KBKDGh@m@x@{@HGBCDAFAH?BAFADCHEFGBCDG??BCDIDKDIBK@O@K?M?M?K@I@GBKBINSn@y@f@aAd@s@v@_AHKz@_AJOFK@GLMFI??pB}BvBAj@J\\P^f@????rBbD????z@lBB`AKd@{@bAUf@_@lDp@b@f@n@tA_B????~EmFlKqJu@wA}@k@cA@{@b@}@j@??YZk@`A]v@O`AAp@B`AH~@??D\\DEzIeInBT????V?PLnCbH^jA??TbAPn@NTNTDPJXTl@~@xB`ArB~CvH??f@zAl@xAnCrGTn@LTNf@Ff@??DNDl@@`CgAzKAJG@EDEDCHAH?F@HBHBD{@zEQb@Q`@[b@????IJc@j@INUf@Ib@Mt@EXCd@A~HJ|@d@zBDTB\\@T?tB@R?V??CpBiDB??{DC????sEBqEABc@Bu@@S??@sDB{AAsAASG]M]MOOKSIUC??S@WHOLGFOXGTEX?jJ?????tB??uA?uB?K?[AO???SOECACCCCEAICGEg@@iC?mDAaG???yHCQZK|ADd@A??|@??{@qBBy@EWE@~@[JKOUC{DB{JnBW@WCg@QYSQQ_@s@Mi@I_A?_C?}DHe@@I?CxE?Z???D?v@EjAQrDu@pB]??~Ci@pCAp@f@t@bCVZRLh@Dd@Gr@m@')
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      

