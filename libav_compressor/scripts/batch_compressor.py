#!/usr/bin/env python
import sched, time, os, sys
import shutil # for debugging, saving the original images

def callback(sc, impath, nbr):
    # schedule new callback in 20s
    sc.enter(20, 1, callback, (sc, impath, nbr+1))
    print "Compressing..."
    temps = []
    first = ""
    counter = 0
    flist = os.listdir(impath)
    rgblist = filter(lambda s: s[:3] == "rgb", flist) # maybe do the filtering at the same time
    rgblist.sort(key = lambda s: int(s[3:9])) # find rgb images, sort them
    flist = filter(lambda s: s[:5] == "depth", flist)
    flist.sort(key = lambda s: int(s[5:11])) # find depth images, sort them
    for f in flist:
        if not os.path.isfile(os.path.join(impath, f)): # should not happen
            continue
        if counter == 0:
            # need to do this here because we need first timestamp
            first = f[12:22]
            timepath = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "videos", "time%s.txt" % first))
            timef = open(timepath, 'w') # open timestamp file for writing
        timef.write(f[:33] + '\n') # write depth filename
        # temporary depth image filename
        depthtemp = os.path.join(impath, "tempdepth%06d.png" % counter)
        # temporary rgb image filename
        rgbtemp = os.path.join(impath, "temprgb%06d.png" % counter)
        ind = -1
        for i, r in enumerate(rgblist): # find corresponding rgb image
            if r[3:9] == f[5:11]:
                ind = i
                rgbf = r
                break
        if ind == -1: # should not happen since rgb is always written before depth
            print "Couldn't find a matching rgb file!"
        rgblist.pop(ind)
        timef.write(rgbf[:31] + '\n') # write rgb filename
        os.rename(os.path.join(impath, f), depthtemp) # rename to know what to compress
        os.rename(os.path.join(impath, rgbf), rgbtemp)
        shutil.copy(depthtemp, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "debug", f))) # for debugging, saving the original images
        shutil.copy(rgbtemp, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "debug", rgbf))) # for debugging, saving the original images
        temps.append(depthtemp) # for later removal
        temps.append(rgbtemp) # for later removal
        counter += 1
    timef.close()
    depthimages = os.path.join(impath, "tempdepth%06d.png") # formatting of files for libav
    rgbimages = os.path.join(impath, "temprgb%06d.png")
    # the path to the libav convenience tool
    avconv = os.path.abspath(os.path.join(os.path.expanduser('~'), "libav", "bin", "avconv"))
    # depth video filename with timestamp
    depthvideo = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "videos", "depth%s.mkv" % first))
    # rgb video filename
    rgbvideo = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "videos", "rgb%s.mov" % first)) # maybe this has to be mkv??
    # compress depth video
    os.system("%s -r 30 -i %s -pix_fmt gray16 -vsync 1 -vcodec ffv1 -coder 1 %s" % (avconv, depthimages, depthvideo))
    # compress rgb video
    os.system("%s -r 30 -i %s -c:v libx264 -preset ultrafast -crf 0 %s" % (avconv, rgbimages, rgbvideo))
    for f in temps: # remove compressed images
        os.remove(f)

def batch_compressor(argv):
    # schedule callback in 20s
    s = sched.scheduler(time.time, time.sleep)
    nbr = 0
    s.enter(20, 1, callback, (s, argv, nbr))
    s.run()

if __name__ == "__main__":
    batch_compressor(sys.argv[1])
