import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { StatusCard } from '@/components/ui/status-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Terminal from '@/components/shared/terminal/terminal';
import { Shield, AlertTriangle, CheckCircle, Terminal as TerminalIcon, GitPullRequest, Zap } from 'lucide-react';
import { launchHunt } from '@/services/api';

function Dashboard() {
  const [repoUrl, setRepoUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [vulnerability, setVulnerability] = useState<string | null>(null);
  const [testStatus, setTestStatus] = useState<string | null>(null);
  const [scanMode, setScanMode] = useState<'auto' | 'full' | 'detect_only'>('auto');
  const [vulnerabilitiesList, setVulnerabilitiesList] = useState<any[]>([]);
  const [resolvedMode, setResolvedMode] = useState<string | null>(null);
  const [repoStats, setRepoStats] = useState<{ file_count: number; total_lines: number } | null>(null);
  const [prUrl, setPrUrl] = useState<string | null>(null);
  const [patchedFiles, setPatchedFiles] = useState<number>(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setLogs([
      '🚀 Initializing SentinelAI...',
      `🎯 Target: ${repoUrl}`,
      `⚙️  Scan Mode: ${scanMode}`,
      '🕵️  [0] Hunter Agent: Scanning target repository...',
    ]);
    setVulnerability(null);
    setTestStatus(null);
    setVulnerabilitiesList([]);
    setResolvedMode(null);
    setRepoStats(null);
    setPrUrl(null);
    setPatchedFiles(0);
    
    try {
      const data = await launchHunt(repoUrl, scanMode);
      
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
          `✅ Scan Complete! Found ${data.total_vulnerabilities} vulnerabilities.`
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
            <p className="text-muted-foreground">Autonomous Security Remediation Pipeline</p>
          </div>
        </div>

        {/* Form */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex gap-4 mb-4 flex-wrap">
              <label className="flex items-center space-x-2">
                <input 
                  type="radio" 
                  value="auto" 
                  checked={scanMode === 'auto'} 
                  onChange={() => setScanMode('auto')} 
                  className="text-primary accent-primary"
                />
                <span className="text-sm font-medium">Auto (Recommended)</span>
              </label>
              <label className="flex items-center space-x-2">
                <input 
                  type="radio" 
                  value="full" 
                  checked={scanMode === 'full'} 
                  onChange={() => setScanMode('full')} 
                  className="text-primary accent-primary"
                />
                <span className="text-sm font-medium">Full Pipeline</span>
              </label>
              <label className="flex items-center space-x-2">
                <input 
                  type="radio" 
                  value="detect_only" 
                  checked={scanMode === 'detect_only'} 
                  onChange={() => setScanMode('detect_only')} 
                  className="text-primary accent-primary"
                />
                <span className="text-sm font-medium">Detect Only</span>
              </label>
            </div>
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

        {/* Mode Decision Banner */}
        {resolvedMode && repoStats && (
          <Card className={`border-l-4 ${resolvedMode === 'detect_only' ? 'border-l-yellow-500 bg-yellow-500/5' : 'border-l-blue-500 bg-blue-500/5'}`}>
            <CardContent className="py-4 flex items-center space-x-4">
              <Zap className={`w-6 h-6 ${resolvedMode === 'detect_only' ? 'text-yellow-500' : 'text-blue-500'}`} />
              <div>
                <p className="font-semibold text-sm">
                  Mode: {resolvedMode === 'detect_only' ? 'Detection Only' : 'Full Pipeline'}
                </p>
                <p className="text-xs text-muted-foreground">
                  {resolvedMode === 'detect_only'
                    ? `Large repository (${repoStats.file_count} files, ${repoStats.total_lines.toLocaleString()} LOC) — scanning only`
                    : `Small repository (${repoStats.file_count} files, ${repoStats.total_lines.toLocaleString()} LOC) — full remediation`
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        )}

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

        {/* Full Pipeline Result — PR Link */}
        {resolvedMode === 'full' && prUrl && (
          <Card className="border-border border-l-4 border-l-green-500 bg-green-500/5">
            <CardContent className="py-4 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <GitPullRequest className="w-6 h-6 text-green-500" />
                <div>
                  <p className="font-semibold text-sm">Pull Request Created</p>
                  <p className="text-xs text-muted-foreground">Patches Applied: {patchedFiles}</p>
                </div>
              </div>
              <a 
                href={prUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="px-4 py-2 text-sm font-medium bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-colors"
              >
                View Pull Request →
              </a>
            </CardContent>
          </Card>
        )}

        {/* Scan Results Block for detect_only mode */}
        {resolvedMode === 'detect_only' && testStatus === 'scan_complete' && (
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
