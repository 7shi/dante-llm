import sys, os

directories = ["inferno", "purgatorio", "paradiso"]
init = "init.xml"
interval = 10
rangemax = 35
once  = False
retry = True
show  = True
think = None
model = None
language = None
srcdir = None
outdir = None

def parse(parser):
    parser.add_argument("-d", dest="directories", type=str,
                        help="specify sub directory (space-separated)")
    parser.add_argument("-i", dest="init", type=str, default="init.xml",
                        help="specify init.xml (default: init.xml)")
    parser.add_argument("-m", dest="model", type=str, required=True,
                        help="specify model name (required)")
    parser.add_argument("-n", dest="interval", type=int, default=10,
                        help="specify interval (default: 10)")
    parser.add_argument("-r", dest="rangemax", type=int, default=35,
                        help="specify range (default: 35)")
    parser.add_argument("-1", dest="once", action="store_true",
                        help="just do one canto")
    parser.add_argument("--no-retry", dest="retry", action="store_false", default=True,
                        help="don't retry queries")
    parser.add_argument("--no-show", dest="show", action="store_false", default=True,
                        help="don't show queries and responses")
    parser.add_argument("--no-think", dest="think", action="store_false", default=None,
                        help="don't include thoughts in response")
    parser.add_argument("language", type=str,
                        help="target language")
    parser.add_argument("srcdir", type=str,
                        help="source directory")
    parser.add_argument("outdir", type=str,
                        help="output directory")

def apply(args):
    global directories, init, interval, rangemax, once, retry, show, think, model, language, srcdir, outdir

    if args.directories:
        directories = args.directories.split()
    init = args.init
    interval = args.interval
    rangemax = args.rangemax
    once = args.once
    retry = args.retry
    show = args.show
    think = args.think
    model = args.model
    language = args.language
    srcdir = args.srcdir
    outdir = args.outdir

    if not os.path.exists(outdir):
        os.mkdir(outdir)

def proc(f):
    global directory, canto, info
    for directory in directories:
        diru = directory[0].upper() + directory[1:]
        path_s = os.path.join(srcdir, directory)
        if not os.path.exists(path_s):
            continue
        path_o = os.path.join(outdir, directory)
        if not os.path.exists(path_o):
            os.mkdir(path_o)
        for canto in range(1, rangemax + 1):
            src = os.path.join(path_s, f"{canto:02}.xml")
            if not os.path.exists(src):
                src = src[:-3] + "txt"
            if not os.path.exists(src):
                break
            xml = os.path.join(path_o, f"{canto:02}.xml")
            if os.path.exists(xml):
                continue
            print()
            info = f"{diru} Canto {canto}"
            print("#", info)
            f(src, xml)
            if once:
                sys.exit(0)
