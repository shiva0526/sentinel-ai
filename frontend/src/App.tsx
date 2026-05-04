import { useState } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { StatusCard } from '@/components/ui/status-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Terminal from '@/components/shared/terminal/terminal';
import { Shield, AlertTriangle, CheckCircle, Terminal as TerminalIcon } from 'lucide-react';

function App() {
  const [repoUrl, setRepoUrl] = useState('https://raw.githubusercontent.com/s4n7h0/Damn-Vulnerable-Python-Web-App/master/app.py');
  const [isLoading, setIsLoading] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [vulnerability, setVulnerability] = useState<string | null>(null);
  const [testStatus, setTestStatus] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setLogs(['🚀 Initializing SentinelAI...', `🎯 Target: ${repoUrl}`, '🕵️  [1] Hunter Agent: Scanning target repository...']);
    setVulnerability(null);
    setTestStatus(null);
    
    try {
      const response = await axios.post('http://localhost:8000/hunt', { repo_url: repoUrl });
      
      const data = response.data;
      setVulnerability(data.vulnerability_found);
      setTestStatus(data.test_status);
      
      // Add the success/failure logs
      setLogs(prev => [
        ...prev, 
        `🚨 Bug Found: ${data.vulnerability_found}`,
        `🔧 Mechanic Agent: Generating patch...`,
        `🥷  Hacker Agent: Writing exploit payload...`,
        `⚖️  Referee: Testing in Sandbox...`,
        `Sandbox Result: ${data.test_status}`,
        data.test_status === 'PASS' 
          ? '✅ Patch held! Ready to deploy.' 
          : '❌ Patch failed! Exploit successful.'
      ]);
      
    } catch (error: any) {
      setLogs(prev => [...prev, `❌ Error: ${error.message}`]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="dark min-h-screen bg-background text-foreground p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center space-x-4">
          <Shield className="w-12 h-12 text-primary" />
          <div>
            <h1 className="text-3xl font-bold tracking-tight">SentinelAI</h1>
            <p className="text-muted-foreground">Autonomous Security Remediation Pipeline</p>
          </div>
        </div>

        {/* Form */}
        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="flex gap-4">
              <Input 
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="Enter GitHub Repository URL"
                className="flex-1"
              />
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Hunting...' : 'Launch SentinelAI'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Grid for Status and Logs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="space-y-4">
            <StatusCard 
              title={vulnerability ? `Vulnerability: ${vulnerability}` : "Awaiting Target"}
              description="Hunter Agent Findings"
              icon={<AlertTriangle className="w-8 h-8 text-yellow-500" />}
            />
            <StatusCard 
              title={testStatus ? `Test: ${testStatus}` : "Awaiting Sandbox"}
              description="Go Sandbox Verification"
              icon={<CheckCircle className={`w-8 h-8 ${testStatus === 'PASS' ? 'text-green-500' : 'text-muted-foreground'}`} />}
            />
          </div>

          <div className="md:col-span-2">
            <Card className="h-full border-border flex flex-col overflow-hidden">
              <CardHeader className="py-3 px-4 border-b bg-muted/50">
                <CardTitle className="text-sm font-mono flex items-center space-x-2">
                  <TerminalIcon className="w-4 h-4" />
                  <span>War Room Terminal</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 p-0 relative min-h-[400px] bg-black">
                <Terminal logs={logs} className="absolute inset-0 p-4" />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
