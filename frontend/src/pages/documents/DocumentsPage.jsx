// ── DocumentsPage.jsx ─────────────────────────────────────
// Documents page: search, filters, grid/list toggle, CRUD, pagination.

import { useState, useMemo } from 'react';
import { useDocuments } from '../../hooks/useDocuments';
import { useDebounce } from '../../hooks/useDebounce';
import { useModal } from '../../hooks/useModal';
import { usePagination } from '../../hooks/usePagination';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Modal } from '../../components/ui/Modal';
import { formatRelativeTime, formatDate, truncate } from '../../utils/formatters';
import { validateDocTitle } from '../../utils/validators';
import {
  Search, LayoutGrid, List, Plus, Pencil, Trash2,
  FolderOpen, Trash, ChevronLeft, ChevronRight, X
} from 'lucide-react';
import styles from './DocumentsPage.module.css';

const STATUS_OPTIONS = ['all', 'published', 'draft', 'archived'];

export function DocumentsPage() {
  const { documents, createDocument, updateDocument, deleteDocument, allTags } = useDocuments();
  const createModal = useModal();
  const editModal   = useModal();
  const deleteModal = useModal();

  const [search, setSearch]       = useState('');
  const [statusFilter, setStatus] = useState('all');
  const [tagFilter, setTag]       = useState('');
  const [viewMode, setViewMode]   = useState('grid'); // 'grid' | 'list'

  const debouncedSearch = useDebounce(search, 300);

  const filtered = useMemo(() => {
    return documents.filter(doc => {
      const q = debouncedSearch.toLowerCase();
      const matchesSearch =
        !q ||
        doc.title.toLowerCase().includes(q) ||
        doc.content.toLowerCase().includes(q) ||
        doc.tags.some(t => t.toLowerCase().includes(q));
      const matchesStatus = statusFilter === 'all' || doc.status === statusFilter;
      const matchesTag    = !tagFilter || doc.tags.includes(tagFilter);
      return matchesSearch && matchesStatus && matchesTag;
    });
  }, [documents, debouncedSearch, statusFilter, tagFilter]);

  const { page, totalPages, paginatedData, prev, next, goTo } = usePagination(filtered, 8);

  // Create form state
  const [createForm, setCreateForm] = useState({ title: '', content: '', tags: '', status: 'draft' });
  const [createErrors, setCreateErrors] = useState({});
  const [isCreating, setIsCreating] = useState(false);

  const handleCreate = (e) => {
    e.preventDefault();
    const titleErr = validateDocTitle(createForm.title);
    if (titleErr) { setCreateErrors({ title: titleErr }); return; }
    setIsCreating(true);
    setTimeout(() => {
      createDocument({
        title: createForm.title.trim(),
        content: createForm.content.trim(),
        tags: createForm.tags.split(',').map(t => t.trim()).filter(Boolean),
        status: createForm.status,
      });
      setCreateForm({ title: '', content: '', tags: '', status: 'draft' });
      setCreateErrors({});
      setIsCreating(false);
      createModal.close();
    }, 400);
  };

  // Edit form state
  const [editForm, setEditForm]     = useState({});
  const [editErrors, setEditErrors] = useState({});
  const [isSaving, setIsSaving]     = useState(false);

  const openEdit = (doc) => {
    setEditForm({ ...doc, tags: doc.tags.join(', ') });
    setEditErrors({});
    editModal.open(doc);
  };

  const handleEdit = (e) => {
    e.preventDefault();
    const titleErr = validateDocTitle(editForm.title);
    if (titleErr) { setEditErrors({ title: titleErr }); return; }
    setIsSaving(true);
    setTimeout(() => {
      updateDocument(editModal.payload.id, {
        title: editForm.title.trim(),
        content: editForm.content.trim(),
        tags: editForm.tags.split(',').map(t => t.trim()).filter(Boolean),
        status: editForm.status,
      });
      setIsSaving(false);
      editModal.close();
    }, 400);
  };

  // Delete
  const [isDeleting, setIsDeleting] = useState(false);
  const handleDelete = () => {
    setIsDeleting(true);
    setTimeout(() => {
      deleteDocument(deleteModal.payload.id);
      setIsDeleting(false);
      deleteModal.close();
    }, 300);
  };

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <div className={styles.toolbarLeft}>
          <Input
            type="search"
            placeholder="Search documents…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            leftIcon={<Search size={16} strokeWidth={2} />}
            aria-label="Search documents"
            containerClassName={styles.searchInput}
          />
        </div>
        <div className={styles.toolbarRight}>
          <div className={styles.viewToggle} role="group" aria-label="View mode">
            <button
              type="button"
              className={[styles.viewBtn, viewMode === 'grid' ? styles.activeView : ''].filter(Boolean).join(' ')}
              onClick={() => setViewMode('grid')}
              aria-pressed={viewMode === 'grid'}
              title="Grid view"
            >
              <LayoutGrid size={16} strokeWidth={2} />
            </button>
            <button
              type="button"
              className={[styles.viewBtn, viewMode === 'list' ? styles.activeView : ''].filter(Boolean).join(' ')}
              onClick={() => setViewMode('list')}
              aria-pressed={viewMode === 'list'}
              title="List view"
            >
              <List size={16} strokeWidth={2} />
            </button>
          </div>
          <Button variant="primary" size="md" leftIcon={<Plus size={16} strokeWidth={2.5} />} onClick={createModal.open}>
            New Doc
          </Button>
        </div>
      </div>

      <div className={styles.filters}>
        <div className={styles.statusFilters} role="group" aria-label="Status filter">
          {STATUS_OPTIONS.map(s => (
            <button
              key={s}
              type="button"
              className={[styles.filterChip, statusFilter === s ? styles.activeChip : ''].filter(Boolean).join(' ')}
              onClick={() => setStatus(s)}
            >
              {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
        {allTags.length > 0 && (
          <select
            className={styles.tagSelect}
            value={tagFilter}
            onChange={e => setTag(e.target.value)}
            aria-label="Filter by tag"
          >
            <option value="">All tags</option>
            {allTags.map(tag => <option key={tag} value={tag}>{tag}</option>)}
          </select>
        )}
        <span className={styles.resultCount}>
          {filtered.length} document{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {paginatedData.length === 0 ? (
        <div className={styles.empty}>
          <span className={styles.emptyIcon}>
            <FolderOpen size={28} strokeWidth={2} />
          </span>
          <p className={styles.emptyText}>No documents found.</p>
          <Button variant="outline" size="sm" onClick={() => { setSearch(''); setStatus('all'); setTag(''); }}>
            Clear filters
          </Button>
        </div>
      ) : (
        <div className={viewMode === 'grid' ? styles.grid : styles.list}>
          {paginatedData.map(doc => (
            <Card key={doc.id} hover className={`${styles.docCard} animate-fade-in`}>
              <div className={styles.cardTop}>
                <div className={styles.cardMeta}>
                  <Badge variant={doc.status} dot>{doc.status}</Badge>
                  <span className={styles.docDate}>{formatRelativeTime(doc.updatedAt)}</span>
                </div>
                <div className={styles.cardActions}>
                  <button
                    type="button"
                    className={styles.actionBtn}
                    onClick={() => openEdit(doc)}
                    aria-label={`Edit "${doc.title}"`}
                    title="Edit"
                  >
                    <Pencil size={13} strokeWidth={2.5} />
                  </button>
                  <button
                    type="button"
                    className={`${styles.actionBtn} ${styles.deleteBtn}`}
                    onClick={() => deleteModal.open(doc)}
                    aria-label={`Delete "${doc.title}"`}
                    title="Delete"
                  >
                    <Trash2 size={13} strokeWidth={2.5} />
                  </button>
                </div>
              </div>

              <h3 className={styles.docTitle}>{doc.title}</h3>
              <p className={styles.docContent}>{truncate(doc.content, viewMode === 'grid' ? 100 : 160)}</p>

              <div className={styles.cardBottom}>
                <div className={styles.docTags}>
                  {doc.tags.slice(0, 3).map(tag => (
                    <Badge key={tag} variant="default">{tag}</Badge>
                  ))}
                  {doc.tags.length > 3 && (
                    <Badge variant="default">+{doc.tags.length - 3}</Badge>
                  )}
                </div>
                <span className={styles.docFullDate}>{formatDate(doc.createdAt)}</span>
              </div>
            </Card>
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <nav className={styles.pagination} aria-label="Document pages">
          <button
            type="button"
            className={styles.pageBtn}
            onClick={prev}
            disabled={page === 1}
            aria-label="Previous page"
          >
            <ChevronLeft size={15} strokeWidth={2.5} style={{ display: 'inline' }} /> Prev
          </button>
          <div className={styles.pageNumbers}>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(n => (
              <button
                key={n}
                type="button"
                className={[styles.pageNum, page === n ? styles.activePage : ''].filter(Boolean).join(' ')}
                onClick={() => goTo(n)}
                aria-label={`Page ${n}`}
                aria-current={page === n ? 'page' : undefined}
              >
                {n}
              </button>
            ))}
          </div>
          <button
            type="button"
            className={styles.pageBtn}
            onClick={next}
            disabled={page === totalPages}
            aria-label="Next page"
          >
            Next <ChevronRight size={15} strokeWidth={2.5} style={{ display: 'inline' }} />
          </button>
        </nav>
      )}

      <Modal isOpen={createModal.isOpen} onClose={createModal.close} title="New Document" size="md">
        <form onSubmit={handleCreate} className={styles.docForm} noValidate>
          <Input
            label="Title"
            type="text"
            value={createForm.title}
            onChange={e => setCreateForm(f => ({ ...f, title: e.target.value }))}
            error={createErrors.title}
            placeholder="Document title…"
            required
            autoFocus
          />
          <div className={styles.fieldGroup}>
            <label className={styles.fieldLabel} htmlFor="create-status">Status</label>
            <select
              id="create-status"
              className={styles.select}
              value={createForm.status}
              onChange={e => setCreateForm(f => ({ ...f, status: e.target.value }))}
            >
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          <div className={styles.fieldGroup}>
            <label className={styles.fieldLabel} htmlFor="create-tags">Tags</label>
            <input
              id="create-tags"
              className={styles.textInput}
              type="text"
              value={createForm.tags}
              onChange={e => setCreateForm(f => ({ ...f, tags: e.target.value }))}
              placeholder="api, design, planning (comma-separated)"
            />
          </div>
          <div className={styles.fieldGroup}>
            <label className={styles.fieldLabel} htmlFor="create-content">Content</label>
            <textarea
              id="create-content"
              className={styles.textarea}
              rows={5}
              value={createForm.content}
              onChange={e => setCreateForm(f => ({ ...f, content: e.target.value }))}
              placeholder="Start writing your document…"
            />
          </div>
          <div className={styles.modalActions}>
            <Button type="button" variant="ghost" onClick={createModal.close}>Cancel</Button>
            <Button type="submit" variant="primary" loading={isCreating}>Create Document</Button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={editModal.isOpen} onClose={editModal.close} title="Edit Document" size="md">
        <form onSubmit={handleEdit} className={styles.docForm} noValidate>
          <Input
            label="Title"
            type="text"
            value={editForm.title || ''}
            onChange={e => setEditForm(f => ({ ...f, title: e.target.value }))}
            error={editErrors.title}
            placeholder="Document title…"
            required
            autoFocus
          />
          <div className={styles.fieldGroup}>
            <label className={styles.fieldLabel} htmlFor="edit-status">Status</label>
            <select
              id="edit-status"
              className={styles.select}
              value={editForm.status || 'draft'}
              onChange={e => setEditForm(f => ({ ...f, status: e.target.value }))}
            >
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          <div className={styles.fieldGroup}>
            <label className={styles.fieldLabel} htmlFor="edit-tags">Tags</label>
            <input
              id="edit-tags"
              className={styles.textInput}
              type="text"
              value={editForm.tags || ''}
              onChange={e => setEditForm(f => ({ ...f, tags: e.target.value }))}
              placeholder="api, design, planning"
            />
          </div>
          <div className={styles.fieldGroup}>
            <label className={styles.fieldLabel} htmlFor="edit-content">Content</label>
            <textarea
              id="edit-content"
              className={styles.textarea}
              rows={5}
              value={editForm.content || ''}
              onChange={e => setEditForm(f => ({ ...f, content: e.target.value }))}
            />
          </div>
          <div className={styles.modalActions}>
            <Button type="button" variant="ghost" onClick={editModal.close}>Cancel</Button>
            <Button type="submit" variant="primary" loading={isSaving}>Save Changes</Button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={deleteModal.isOpen} onClose={deleteModal.close} title="Delete Document" size="sm">
        <div className={styles.deleteConfirm}>
          <span className={styles.deleteIcon} aria-hidden="true">
            <Trash size={28} strokeWidth={2.5} />
          </span>
          <p className={styles.deleteText}>
            Are you sure you want to delete{' '}
            <strong>"{deleteModal.payload?.title}"</strong>?
            This action cannot be undone.
          </p>
          <div className={styles.modalActions}>
            <Button type="button" variant="ghost" onClick={deleteModal.close}>Cancel</Button>
            <Button type="button" variant="danger" loading={isDeleting} onClick={handleDelete}>
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
