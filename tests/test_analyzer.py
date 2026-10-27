import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from http.client import HTTPConnection
from pathlib import Path
from flakewise.analyzer import analyze, InputError, classify_counts
from server import App

PASS = Path('examples/pass.xml').read_text()
FAIL = Path('examples/fail.xml').read_text()

def row(name, commit, xml):
    return {'name':name,'commit':commit,'xml':xml}

class AnalysisTests(unittest.TestCase):
    def test_same_commit_flips_and_stable_counts(self):
        output = analyze({'runs':[row('pass','ABCDEF123',PASS),row('fail','abcdef123',FAIL)]})
        self.assertEqual(output['summary'], {'runs':2,'tests':2,'mixed':1,'failed':0,'passed':1,'insufficient':0,'skipped':0})
        case = output['tests'][0]
        self.assertEqual(case['classification'], 'mixed')
        self.assertEqual([o['status'] for o in case['observations']], ['pass','fail'])
        self.assertEqual(case['observations'][1]['message'], 'Expected one payment, found two')
        self.assertTrue(any('not independently verified' in w for w in output['warnings']))
    def test_different_commits_never_merged(self):
        output = analyze({'runs':[row('a','abcdef123',PASS),row('b','fedcba987',FAIL)]})
        self.assertEqual(output['summary']['mixed'],0)
        self.assertEqual(output['summary']['insufficient'],4)
    def test_count_semantics(self):
        for counts, expected in [((1,1,0),'mixed'),((1,0,0),'insufficient'),((0,1,3),'insufficient'),((2,0,0),'passed'),((0,2,0),'failed'),((0,0,2),'skipped')]:
            with self.subTest(counts=counts): self.assertEqual(classify_counts(*counts),expected)
    def test_skipped_and_error(self):
        xml = '<testsuite><testcase classname="c" name="s"><skipped/></testcase><testcase classname="c" name="e"><error message="timeout"/></testcase></testsuite>'
        data = analyze({'runs':[row('r','abcdef123',xml)]})
        by_name = {x['name']:x for x in data['tests']}
        self.assertEqual(by_name['s']['classification'],'skipped')
        self.assertEqual(by_name['e']['observations'][0]['status'],'fail')
        self.assertEqual(by_name['e']['classification'],'insufficient')
    def test_rejects_hostile_dtd_and_entities(self):
        for xml in ['<!DOCTYPE testsuite [<!ENTITY x "explode">]><testsuite>&x;</testsuite>', '<!ENTITY x "x"><testsuite/>']:
            with self.subTest(xml=xml), self.assertRaises(InputError): analyze({'runs':[row('r','abcdef123',xml)]})
    def test_rejects_duplicate_identity_within_run(self):
        xml = '<testsuite><testcase classname="c" name="n"/><testcase classname="c" name="n"><failure/></testcase></testsuite>'
        with self.assertRaisesRegex(InputError,'Duplicate'): analyze({'runs':[row('r','abcdef123',xml)]})
    def test_rejects_invalid_and_oversized_inputs(self):
        for data in [{'runs':[]}, {'runs':[row('r','main',PASS)]}, {'runs':[row('r','abcdef123',PASS),row('r','abcdef123',PASS)]}, {'runs':[row('r','abcdef123','x'*524289)]}, {'runs':[row('r','abcdef123','<notjunit/>')]}, {'runs':[row('r','abcdef123','<testsuite><testcase name="a" time="NaN"/></testsuite>')]}]:
            with self.subTest(data=str(data)[:80]), self.assertRaises(InputError): analyze(data)
    def test_rejects_unpaired_surrogate(self):
        with self.assertRaises(InputError): analyze({'runs':[row('r','abcdef123','<testsuite>\ud800</testsuite>')]})
    def test_rejects_long_names_instead_of_merging_prefixes(self):
        for attr in ('name','classname'):
            xml = '<testsuite><testcase name="test" classname="Class"/></testsuite>'
            xml = xml.replace(f'{attr}="' + ('test' if attr == 'name' else 'Class') + '"', f'{attr}="' + 'x'*501 + '"')
            with self.subTest(attr=attr), self.assertRaisesRegex(InputError, '500-character'):
                analyze({'runs':[row('a','abcdef123',xml)]})
    def test_classless_tests_use_named_suite_identity(self):
        def report(suite, body=''):
            return f'<testsuite name="{suite}"><testcase name="same">{body}</testcase></testsuite>'
        different = analyze({'runs':[row('a','abcdef123',report('A')),row('b','abcdef123',report('B','<failure/>'))]})
        self.assertEqual(different['summary']['mixed'],0)
        self.assertEqual(different['summary']['tests'],2)
        same = analyze({'runs':[row('a','abcdef123',report('A')),row('b','abcdef123',report('A','<failure/>'))]})
        self.assertEqual(same['summary']['mixed'],1)
    def test_unqualified_names_remain_separate_by_report(self):
        a = '<testsuite><testcase name="same"/></testsuite>'
        b = '<testsuite><testcase name="same"><failure/></testcase></testsuite>'
        data = analyze({'runs':[row('a','abcdef123',a),row('b','abcdef123',b)]})
        self.assertEqual(data['summary']['mixed'],0)
        self.assertEqual(data['summary']['tests'],2)
        self.assertNotEqual(data['tests'][0]['id'],data['tests'][1]['id'])
        self.assertTrue(any('kept separate by report' in w for w in data['warnings']))
    def test_class_and_suite_namespaces_do_not_collide(self):
        a='<testsuite name="A"><testcase name="same"/></testsuite>'
        b='<testsuite><testcase classname="A" name="same"><failure/></testcase></testsuite>'
        data=analyze({'runs':[row('a','abcdef123',a),row('b','abcdef123',b)]})
        self.assertEqual(data['summary']['mixed'],0)
    def test_deep_named_suite_paths_are_bounded(self):
        xml='<testsuite name="s">'*41+'<testcase name="a"/>'+'</testsuite>'*41
        with self.assertRaisesRegex(InputError,'nesting'): analyze({'runs':[row('a','abcdef123',xml)]})
    def test_retry_extensions_not_silently_treated_as_pass(self):
        for marker in ('flakyFailure','flakyError','rerunFailure','rerunError'):
            xml=f'<testsuite><testcase name="a"><{marker} message="intermittent"/></testcase></testsuite>'
            with self.subTest(marker=marker), self.assertRaisesRegex(InputError,'Retry-specific'):
                analyze({'runs':[row('a','abcdef123',xml)]})
    def test_nested_testcase_rejected(self):
        xml='<testsuite><testcase name="outer"><testcase name="inner"><failure/></testcase></testcase></testsuite>'
        with self.assertRaisesRegex(InputError,'Nested'):
            analyze({'runs':[row('a','abcdef123',xml)]})
    def test_untrusted_messages_are_not_html(self):
        xml='<testsuite><testcase name="&lt;img&gt;"><failure message="&lt;script&gt;"/></testcase></testsuite>'
        t=analyze({'runs':[row('r','abcdef123',xml)]})['tests'][0]
        self.assertEqual(t['name'],'<img>')
        self.assertEqual(t['observations'][0]['message'],'<script>')

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = ThreadingHTTPServer(('127.0.0.1',0), App)
        cls.thread=threading.Thread(target=cls.s.serve_forever, daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls): cls.s.shutdown();cls.s.server_close();cls.thread.join()
    def post(self, body, headers=None):
        c=HTTPConnection('127.0.0.1',self.s.server_port,timeout=5)
        c.request('POST','/api/analyze',body,headers or {'Content-Type':'application/json'})
        response=c.getresponse();content=response.read();status=response.status;c.close();return status,json.loads(content)
    def test_full_api(self):
        status,result=self.post(json.dumps({'runs':[row('a','abcdef123',PASS),row('b','abcdef123',FAIL)]}))
        self.assertEqual(status,200);self.assertEqual(result['summary']['mixed'],1)
    def test_origin_and_bad_json(self):
        self.assertEqual(self.post('{}',{'Content-Type':'application/json','Origin':'https://evil.example'})[0],403)
        self.assertEqual(self.post('{"runs":[],"runs":[]}')[0],400)
        self.assertEqual(self.post('{}',{'Content-Type':'text/plain'})[0],415)
if __name__ == '__main__': unittest.main()
