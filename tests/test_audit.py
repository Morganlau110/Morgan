import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from sros_audit.inventory import load_inventory
from sros_audit.parsers import parse, ParseError
from sros_audit.runner import audit, inspect_device
from sros_audit.transport import MockTransport, SSHTransport
from sros_audit.health import evaluate
from sros_audit.cli import main
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def setUp(self): self.devices=load_inventory(ROOT/'examples/inventory.json')
 def test_integration(self):
  r=audit(self.devices)
  self.assertEqual(r['summary'],dict(healthy=1,warning=0,critical=1,error=0))
  self.assertEqual({f['code'] for f in r['devices'][1]['findings']},{'PORT_DOWN','LAG_DEGRADED','BGP_NOT_ESTABLISHED'})
  self.assertEqual(r['devices'][0]['bgp_summary']['received_sum_per_peer'],150)
 def test_disabled_port(self): self.assertEqual(evaluate({'ports':[dict(id='x',admin='down',oper='down')]}),[])
 def test_minimum(self): self.assertEqual(evaluate({'lags':[dict(id='x',admin='up',oper='up',active=1,total=2,minimum=2)]})[0]['code'],'LAG_UNAVAILABLE')
 def test_zero(self): self.assertEqual(parse('bgp','Neighbor AS State Received Active Sent\nTotal: 0'),[])
 def test_bad_tables(self):
  for text in ('','garbage','Port Admin Oper Description\n1/1/1 up up x','Port Admin Oper Description\nTotal: 1','Port Admin Oper Description\n1/1/1 bad up x\nTotal: 1','Port Admin Oper Description\n1/1/1 up up x\n1/1/1 up up x\nTotal: 2'):
   with self.subTest(text=text),self.assertRaises(ParseError): parse('ports',text)
 def test_bad_bgp(self):
  for row in ('bad 64512 Established 1 1 1','192.0.2.1 64512 Established -1 0 0','192.0.2.1 64512 Established - - -'):
   with self.subTest(row=row),self.assertRaises(ParseError): parse('bgp','Neighbor AS State Received Active Sent\n'+row+'\nTotal: 1')
 def test_inventory(self):
  for devices in ([],[{'name':'../x'}],[{'name':'x','password':'secret'}],[{'name':'x','fixture':'../'}],[{'name':'x','transport':'telnet'}],[dict(name='x',transport='ssh',host='a',username='b',port=0)]):
   with tempfile.TemporaryDirectory() as d:
    p=Path(d)/'i.json';p.write_text(json.dumps({'devices':devices}))
    with self.subTest(devices=devices),self.assertRaises(ValueError): load_inventory(p)
 def test_allowlist(self):
  with self.assertRaises(ValueError): MockTransport(self.devices[0]).run('configure shutdown')
 def test_error_isolation_redaction(self):
  def factory(d):
   if d['name'].endswith('02'): raise RuntimeError('secret-password')
   return MockTransport(d)
  r=audit(self.devices,factory)
  self.assertEqual(r['summary']['healthy'],1);self.assertEqual(r['summary']['error'],1)
  self.assertNotIn('secret-password',json.dumps(r));self.assertIsNone(r['devices'][1]['bgp_summary'])
 def test_partial_failure_cleanup(self):
  class Broken(MockTransport):
   closed=False
   def run(self,c): return 'bad' if 'bgp' in c else super().run(c)
   def close(self): self.closed=True
  t=Broken(self.devices[0]);r=inspect_device(self.devices[0],lambda _:t)
  self.assertEqual(r['status'],'error');self.assertIn('ports',r['data']);self.assertTrue(t.closed)
 def test_cli(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'report.json'
   self.assertEqual(main(['--inventory',str(ROOT/'examples/inventory.json'),'--output',str(p)]),1)
   self.assertEqual(json.loads(p.read_text())['schema_version'],'1.0')
 def test_ssh_opt_in(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'i.json';p.write_text(json.dumps({'devices':[dict(name='x',transport='ssh',host='192.0.2.1',username='audit')]}))
   with patch('sros_audit.cli.audit') as run,self.assertRaises(SystemExit) as e: main(['--inventory',str(p)])
   self.assertEqual(e.exception.code,2);run.assert_not_called()
 def test_ssh_verification(self):
  m=MagicMock()
  with patch.dict('sys.modules',{'paramiko':m}):
   t=SSHTransport(dict(host='192.0.2.1',username='audit'))
   m.SSHClient.return_value.set_missing_host_key_policy.assert_called_once_with(m.RejectPolicy.return_value)
   with self.assertRaises(ValueError): t.run('show port; configure')
   t.close()
