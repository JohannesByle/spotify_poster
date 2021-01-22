# spotify_poster
Functions for turning your spotify data into a poster of your most listened to albums or artists

## Features
1. Filtering by artist genres, for example choose to only include albums from artists whose genres include "rock" and "80's"
2. Mix and match poster styles. Configuration options include:
    1. Album sizes directly proportional to listen time.
    2. Album sized roughly proportional to listen time but evenly spaced.
    3. Apply a color filter to each poster propotional to listen time.
    4. Order albums in multiple different ways: distance from point, manhattan distance from point, sequential, random etc.
3. Easily extensible. Have an idea for a poster you want to make, simply add a function to the `Poster` class.
