// ── DashboardPage.jsx ─────────────────────────────────────
// Main dashboard: welcome card, stat cards, quick actions, recent docs.

import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useDocuments } from '../../hooks/useDocuments';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { formatRelativeTime, truncate } from '../../utils/formatters';
import { FileText, CheckCircle, PenLine, Archive, Inbox, Plus } from 'lucide-react';
import styles from './DashboardPage.module.css';

const STAT_CARDS = (stats) => [
  {
    label: 'Total Documents',
    value: stats.total,
    Icon: FileText,
    desc: `${stats.draft} drafts`,
  },
  {
    label: 'Published',
    value: stats.published,
    Icon: CheckCircle,
    desc: 'Live documents',
  },
  {
    label: 'Drafts',
    value: stats.draft,
    Icon: PenLine,
    desc: 'In progress',
  },
  {
    label: 'Archived',
    value: stats.archived,
    Icon: Archive,
    desc: 'Stored away',
  },
];

export function DashboardPage() {
  const { user } = useAuth();
  const { documents, stats } = useDocuments();
  const recentDocs = documents.slice(0, 5);
  const firstName = user?.name?.split(' ')[0] || 'there';

  return (
    <div className={styles.page}>
      {/* Welcome banner */}
      <section className={`${styles.welcome} animate-fade-in`}>
        <div className={styles.welcomeText}>
          <h2 className={styles.greeting}>Good day, {firstName}!</h2>
          <p className={styles.subtitle}>
            Here's what's happening with your workspace today.
          </p>
        </div>
        <Link to="/documents">
          <Button variant="ghost" size="md" leftIcon={<Plus size={16} strokeWidth={2.5} />}>
            New Document
          </Button>
        </Link>
      </section>

      {/* Stats grid */}
      <section aria-label="Stats" className={`${styles.statsGrid} stagger-children`}>
        {STAT_CARDS(stats).map((card) => (
          <Card key={card.label} className={`${styles.statCard} animate-fade-in`} hover>
            <div className={styles.statIconWrap}>
              <card.Icon size={22} strokeWidth={2.5} aria-hidden="true" />
            </div>
            <div>
              <div className={styles.statValue}>{card.value}</div>
              <div className={styles.statLabel}>{card.label}</div>
              <div className={styles.statDesc}>{card.desc}</div>
            </div>
          </Card>
        ))}
      </section>

      {/* Recent documents */}
      <section className={styles.recentSection}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Recent Documents</h2>
          <Link to="/documents" className={styles.viewAll}>View all →</Link>
        </div>

        <Card padding="none" className={styles.tableCard}>
          {recentDocs.length === 0 ? (
            <div className={styles.empty}>
              <span className={styles.emptyIcon}>
                <Inbox size={28} strokeWidth={2} />
              </span>
              <p>No documents yet.</p>
              <Link to="/documents"><Button variant="outline" size="sm">Create your first doc</Button></Link>
            </div>
          ) : (
            <div className={styles.tableWrap} role="region" aria-label="Recent documents table">
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th scope="col">Title</th>
                    <th scope="col">Status</th>
                    <th scope="col">Tags</th>
                    <th scope="col">Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {recentDocs.map(doc => (
                    <tr key={doc.id} className={styles.tableRow}>
                      <td>
                        <div className={styles.docTitle}>{doc.title}</div>
                        <div className={styles.docPreview}>{truncate(doc.content, 60)}</div>
                      </td>
                      <td>
                        <Badge variant={doc.status} dot>{doc.status}</Badge>
                      </td>
                      <td>
                        <div className={styles.tags}>
                          {doc.tags.slice(0, 2).map(t => (
                            <Badge key={t} variant="default">{t}</Badge>
                          ))}
                        </div>
                      </td>
                      <td className={styles.updatedAt}>
                        {formatRelativeTime(doc.updatedAt)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </section>
    </div>
  );
}
