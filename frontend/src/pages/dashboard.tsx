import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { StatusCard } from '@/components/ui/status-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Terminal from '@/components/shared/terminal/terminal';
import { Shield, AlertTriangle, CheckCircle, Terminal as TerminalIcon, Zap, Mail } from 'lucide-react';
import { launchHunt } from '@/services/api';

function Dashboard() {
  const [repoUrl, setRepoUrl] = useState('');
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [testStatus, setTestStatus] = useState<string | null>(null);
  const [vulnerabilitiesList, setVulnerabilitiesList] = useState<any[]>([]);
  const [resolvedMode, setResolvedMode] = useState<string | null>(null);
  const [repoStats, setRepoStats] = useState<{ file_count: number; total_lines: number } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setLogs([
      '🚀 Initializing SentinelAI...',
      `🎯 Target: ${repoUrl}`,
      ...(email ? [`📧 Notifications: ${email}`] : []),
      '🕵️  [0] Hunter Agent: Scanning target repository...',
    ]);
    setTestStatus(null);
    setVulnerabilitiesList([]);
    setResolvedMode(null);
    setRepoStats(null);
    
    try {
      const data = await launchHunt(repoUrl, 'auto', email);
      
      if (data.status === 'failed') {
        setLogs(prev => [...prev, `❌ Scan Failed: ${data.error || 'Unknown error'}`]);
        return;
      }

      const mode = data.mode || scanMode;
      setResolvedMode(mode);
      if (data.repo_stats) setRepoStats(data.repo_stats);

      if (mode === 'detect_only') {
        setTestStatus(data.status);
        if (data.vulnerabilities) {
          const priority: Record<string, number> = { Critical: 4, High: 3, Medium: 2, Low: 1 };
          const sorted = [...data.vulnerabilities].sort((a, b) => {
            return (priority[b.confidence] || 0) - (priority[a.confidence] || 0);
          });
          setVulnerabilitiesList(sorted);
        }
        setLogs(prev => [
          ...prev,
          `📊 Repo: ${data.repo_stats?.file_count} files, ${data.repo_stats?.total_lines} LOC`,
          `🔍 Mode selected: Detection Only`,
          `✅ Scan Complete! Found ${data.total_vulnerabilities} vulnerabilities.`,
          ...(email ? ['📧 Email notification sent.'] : []),
        ]);
      } else {
        setVulnerability(data.vulnerability_found || null);
        setTestStatus(data.test_status || null);
        if (data.pr_url) setPrUrl(data.pr_url);
        if (data.patched_files) setPatchedFiles(data.patched_files);
        
        setLogs(prev => [
          ...prev, 
          `📊 Repo: ${data.repo_stats?.file_count} files, ${data.repo_stats?.total_lines} LOC`,
          `🔧 Mode selected: Full Pipeline`,
          `🚨 Bug Found: ${data.vulnerability_found}`,
          `🔧 Mechanic Agent: Patch generated`,
          `🥷  Hacker Agent: Exploit payload written`,
          `⚖️  Validator: Sandbox test complete`,
          `Result: ${data.test_status}`,
          data.test_status === 'PASS' 
            ? '✅ Patch held! Ready to deploy.' 
            : '❌ Patch failed! Exploit successful.',
          ...(data.pr_url ? [`🔗 PR Created: ${data.pr_url}`] : []),
          ...(email ? ['📧 Email notification sent.'] : []),
        ]);
      }
      
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
            <p className="text-muted-foreground">Autonomous Security Scanning Pipeline</p>
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
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email for notifications (optional)"
                  className="pl-10 w-72"
                />
              </div>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Scanning...' : 'Launch SentinelAI'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Mode Decision Banner */}
        {resolvedMode && repoStats && (
          <Card className="border-l-4 border-l-yellow-500 bg-yellow-500/5">
            <CardContent className="py-4 flex items-center space-x-4">
              <Zap className="w-6 h-6 text-yellow-500" />
              <div>
                <p className="font-semibold text-sm">Mode: Detection Only</p>
                <p className="text-xs text-muted-foreground">
                  Repository scanned: {repoStats.file_count} files, {repoStats.total_lines.toLocaleString()} LOC
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Status Cards + Terminal */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="space-y-4">
            <StatusCard 
              title={vulnerabilitiesList.length > 0 ? `Found: ${vulnerabilitiesList.length} vulnerabilities` : "Awaiting Scan"}
              description="Hunter Agent Findings"
              icon={<AlertTriangle className={`w-8 h-8 ${vulnerabilitiesList.length > 0 ? 'text-yellow-500' : 'text-muted-foreground'}`} />}
            />
            <StatusCard 
              title={testStatus === 'scan_complete' ? 'Scan Complete' : 'Awaiting Scan'}
              description="Detection Engine Status"
              icon={<CheckCircle className={`w-8 h-8 ${testStatus === 'scan_complete' ? 'text-green-500' : 'text-muted-foreground'}`} />}
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

        {/* Vulnerability Results */}
        {testStatus === 'scan_complete' && (
          vulnerabilitiesList.length > 0 ? (
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="text-xl flex items-center space-x-2">
                  <AlertTriangle className="w-6 h-6 text-yellow-500" />
                  <span>Scan Results ({vulnerabilitiesList.length} Vulnerabilities)</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {vulnerabilitiesList.map((vuln, i) => (
                  <div key={i} className="p-4 bg-muted/30 rounded-lg border border-border">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-bold text-lg text-red-400">{vuln.type}</h3>
                      <span className={`px-2 py-1 text-xs font-bold rounded-full ${vuln.confidence === 'High' || vuln.confidence === 'Critical' ? 'bg-red-500/20 text-red-400' : vuln.confidence === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-blue-500/20 text-blue-400'}`}>
                        {vuln.confidence} Confidence
                      </span>
                    </div>
                    <div className="text-sm font-mono text-muted-foreground mb-2">
                      File: {vuln.file} <br/>
                      Line: {vuln.line}
                    </div>
                    <p className="text-sm">{vuln.description}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          ) : (
            <Card className="border-border border-green-500/50 bg-green-500/5">
              <CardHeader>
                <CardTitle className="text-xl flex items-center space-x-2 text-green-500">
                  <CheckCircle className="w-6 h-6" />
                  <span>No vulnerabilities found</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">The repository scan completed successfully and no rule-based vulnerabilities were detected.</p>
              </CardContent>
            </Card>
          )
        )}
      </div>
    </div>
  );
}

export default Dashboard;
