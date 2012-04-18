import setup, definitions, sys

def run_tests(module_names, argv):
    for name in module_names:
        test_module = sys.modules[name]
        try:
            print "="*80
            print "Testing module", name
            test_module.setup(argv)
            test_module.run(argv)
            test_module.tear_down(argv)
            print "OK"
        except Exception, e:
            print "Error:", type(e), e.message

def run_setups(module_names, argv):
    for name in module_names:
        test_module = sys.modules[name]
        try:
            print "="*80
            print "Setuping module", name
            test_module.setup(argv)
            print "OK"
        except Exception, e:
            print "Error:", type(e), e.message

def run_tear_downs(module_names, argv):
    for name in module_names:
        test_module = sys.modules[name]
        try:
            print "="*80
            print "Tearing down module", name
            test_module.tear_down(argv)
            print "OK"
        except Exception, e:
            print "Error:", type(e), e.message

def run_tests_only(module_names, argv):
    for name in module_names:
        test_module = sys.modules[name]
        try:
            print "="*80
            print "Testing module (no setup, no tear down)", name
            test_module.run(argv)
            print "OK"
        except Exception, e:
            print "Error:", type(e), e.message

def test_wrapper(module_names):
    """
    """
    setup.setup()
    definitions.define()

    if len(sys.argv) == 1:
        print "No action given"
    else:
        if sys.argv[1] == "setup":
            run_setups(module_names, sys.argv[2:])
        elif sys.argv[1] == "tear_down":
            run_tear_downs(module_names, sys.argv[2:])
        elif sys.argv[1] == "run":
            run_tests_only(module_names, sys.argv[2:])
        elif sys.argv[1] == "all":
            run_tests(module_names, sys.argv[2:])
        else:
            print "Unrecognized action."
            print "Accepted actions: setup, run, tear_down, all"
