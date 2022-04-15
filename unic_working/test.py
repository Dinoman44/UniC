import mpu

latitude1 = 1.3488607
longitude1 = 103.96224869999999

latitude2 = 1.3553352
longitude2 = 103.9482855


# latitude is y
# longitude is x 


dist = mpu.haversine_distance((latitude1, longitude1), (latitude2, longitude2))

print(dist)

