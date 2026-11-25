// ── useDocuments ──────────────────────────────────────────
// CRUD operations for documents, backed by localStorage.

import { useCallback, useMemo } from 'react';
import { useLocalStorage } from './useLocalStorage';

/** Seed data for first-time load */
const SEED_DOCUMENTS = [
  {
    id: '1', title: 'Product Requirements Document', content: 'This document outlines the product requirements for the HoneyPot platform including core features, user flows, and technical specifications.',
    tags: ['product', 'planning'], status: 'published', createdAt: '2026-11-01T10:00:00Z', updatedAt: '2026-11-10T14:00:00Z',
  },
  {
    id: '2', title: 'API Integration Guide', content: 'Step-by-step guide for integrating with the HoneyPot REST API. Covers authentication, rate limiting, and all available endpoints.',
    tags: ['technical', 'api'], status: 'published', createdAt: '2026-11-05T09:00:00Z', updatedAt: '2026-11-12T11:30:00Z',
  },
  {
    id: '3', title: 'Design System Guidelines', content: 'Visual design guidelines including color tokens, typography scale, spacing system, and component usage patterns for consistent UI.',
    tags: ['design', 'ui'], status: 'draft', createdAt: '2026-11-08T13:00:00Z', updatedAt: '2026-11-14T16:00:00Z',
  },
  {
    id: '4', title: 'Security Audit Report', content: 'Comprehensive security audit findings, vulnerabilities identified, risk assessments, and recommended remediation steps.',
    tags: ['security', 'compliance'], status: 'published', createdAt: '2026-11-10T08:00:00Z', updatedAt: '2026-11-15T10:00:00Z',
  },
  {
    id: '5', title: 'Q4 Roadmap Planning', content: 'Strategic roadmap for Q4 2026 outlining milestones, sprint goals, feature priorities, and team allocations.',
    tags: ['planning', 'strategy'], status: 'draft', createdAt: '2026-11-12T12:00:00Z', updatedAt: '2026-11-18T09:00:00Z',
  },
  {
    id: '6', title: 'Deployment Runbook', content: 'Operational runbook for deploying HoneyPot to production. Includes pre-flight checks, rollout steps, and rollback procedures.',
    tags: ['devops', 'technical'], status: 'published', createdAt: '2026-11-15T14:00:00Z', updatedAt: '2026-11-20T08:30:00Z',
  },
  {
    id: '7', title: 'User Research Findings', content: 'Synthesis of 20+ user interviews. Key insights around pain points, mental models, and feature demand from target personas.',
    tags: ['research', 'product'], status: 'archived', createdAt: '2026-11-18T10:00:00Z', updatedAt: '2026-11-22T15:00:00Z',
  },
  {
    id: '8', title: 'Onboarding Checklist', content: 'Step-by-step onboarding guide for new team members. Covers tooling setup, access provisioning, and first-week goals.',
    tags: ['hr', 'process'], status: 'published', createdAt: '2026-11-20T09:00:00Z', updatedAt: '2026-11-24T12:00:00Z',
  },
];

export function useDocuments() {
  const [documents, setDocuments] = useLocalStorage('hp_documents', SEED_DOCUMENTS);

  /** Create a new document */
  const createDocument = useCallback((data) => {
    const doc = {
      id: crypto.randomUUID(),
      title: data.title,
      content: data.content || '',
      tags: data.tags || [],
      status: data.status || 'draft',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setDocuments(prev => [doc, ...prev]);
    return doc;
  }, [setDocuments]);

  /** Update an existing document by id */
  const updateDocument = useCallback((id, updates) => {
    setDocuments(prev =>
      prev.map(doc =>
        doc.id === id
          ? { ...doc, ...updates, updatedAt: new Date().toISOString() }
          : doc
      )
    );
  }, [setDocuments]);

  /** Delete a document by id */
  const deleteDocument = useCallback((id) => {
    setDocuments(prev => prev.filter(doc => doc.id !== id));
  }, [setDocuments]);

  /** Get a single document by id */
  const getDocument = useCallback((id) => {
    return documents.find(doc => doc.id === id) || null;
  }, [documents]);

  /** Summary stats */
  const stats = useMemo(() => ({
    total:     documents.length,
    published: documents.filter(d => d.status === 'published').length,
    draft:     documents.filter(d => d.status === 'draft').length,
    archived:  documents.filter(d => d.status === 'archived').length,
  }), [documents]);

  /** All unique tags */
  const allTags = useMemo(() => {
    const tagSet = new Set(documents.flatMap(d => d.tags));
    return Array.from(tagSet).sort();
  }, [documents]);

  return {
    documents,
    createDocument,
    updateDocument,
    deleteDocument,
    getDocument,
    stats,
    allTags,
  };
}
