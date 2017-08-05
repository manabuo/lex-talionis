# Given a palette, gets largest object in picture composed of that palette

import glob
from PIL import Image
import palette_index

palette_set = palette_index.garcia

for idx, fp in enumerate(sorted(glob.glob('*.png'))):
    print(fp)
    image = Image.open(fp).convert('RGB')
    width, height = image.size
    grid = [False for _ in xrange(width*height)]
    for x in xrange(width):
        for y in xrange(height):
            color = image.getpixel((x, y))
            if color in palette_set:
                grid[y*width + x] = True
            else:
                image.putpixel((x, y), (128, 160, 128))

    print('Determining largest image...')
    count = 0
    set_grid = [0 for _ in xrange(width*height)]
    discrete_images = {}
    for num, present in enumerate(grid):
        if present and not set_grid[num]:
            count += 1
            discrete_images[count] = set()
            x, y = num%width, num/width
            discrete_images[count].add((x, y))
            explored = []
            explored.append(num)
            while explored:
                visit = explored.pop()
                if set_grid[visit]:
                    continue # already visited
                x, y = visit%width, visit/width                    
                set_grid[visit] = count
                # get adjacent
                adjacents = []
                if x > 0: # Left
                    adjacents.append(visit - 1)
                if x < width - 1: # Right
                    adjacents.append(visit + 1)
                if y > 0: # Top
                    adjacents.append(visit - width)
                if y < len(grid)/width - 1: # Bottom
                    adjacents.append(visit + width)
                for adj in adjacents:
                    if grid[adj]:
                        discrete_images[count].add((adj%width, adj/width))
                        explored.append(adj)

    which_count = 0
    current_max = 0
    for count in discrete_images:
        this_length = len(discrete_images[count])
        if this_length > current_max:
            current_max = this_length
            which_count = count

    print('Cropping...')
    for x in xrange(width):
        for y in xrange(height):
            if (x, y) not in discrete_images[which_count]:
                image.putpixel((x, y), (128, 160, 128))

    image.save('Attack' + str(idx) + '.png')
