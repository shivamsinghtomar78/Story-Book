import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Book, Heart, Trash2, Search, Download, Filter, Calendar } from 'lucide-react';
import SkeletonLoader from '../components/SkeletonLoader';

const Library = () => {
    const [stories, setStories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [filter, setFilter] = useState('all'); // all, favorites
    const [sortBy, setSortBy] = useState('created_at');
    const [sortOrder, setSortOrder] = useState('desc');
    const [pagination, setPagination] = useState({});
    const [currentPage, setCurrentPage] = useState(1);
    const [stats, setStats] = useState(null);

    const navigate = useNavigate();

    // Fetch stories
    const fetchStories = async (page = 1) => {
        try {
            setLoading(true);
            const token = localStorage.getItem('token');

            const params = {
                page,
                limit: 12,
                sort_by: sortBy,
                sort_order: sortOrder
            };

            if (filter === 'favorites') {
                params.favorites = 'true';
            }

            const response = await axios.get('/api/stories', {
                headers: { Authorization: `Bearer ${token}` },
                params
            });

            setStories(response.data.stories);
            setPagination(response.data.pagination);
            setCurrentPage(page);
        } catch (error) {
            console.error('Error fetching stories:', error);
        } finally {
            setLoading(false);
        }
    };

    // Fetch stats
    const fetchStats = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await axios.get('/api/stories/stats', {
                headers: { Authorization: `Bearer ${token}` }
            });
            setStats(response.data.stats);
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    };

    // Search stories
    const handleSearch = async (e) => {
        e.preventDefault();
        if (!searchQuery.trim()) {
            fetchStories(1);
            return;
        }

        try {
            setLoading(true);
            const token = localStorage.getItem('token');
            const response = await axios.get('/api/stories/search', {
                headers: { Authorization: `Bearer ${token}` },
                params: { q: searchQuery, limit: 12 }
            });

            setStories(response.data.stories);
            setPagination(response.data.pagination);
        } catch (error) {
            console.error('Error searching:', error);
        } finally {
            setLoading(false);
        }
    };

    // Toggle favorite
    const toggleFavorite = async (storyId, currentStatus) => {
        try {
            const token = localStorage.getItem('token');
            await axios.patch(`/api/story/${storyId}/favorite`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });

            // Update local state
            setStories(stories.map(s =>
                s._id === storyId ? { ...s, is_favorite: !currentStatus } : s
            ));

            // Refresh stats
            fetchStats();
        } catch (error) {
            console.error('Error toggling favorite:', error);
        }
    };

    // Delete story
    const deleteStory = async (storyId) => {
        if (!confirm('Are you sure you want to delete this story?')) return;

        try {
            const token = localStorage.getItem('token');
            await axios.delete(`/api/story/${storyId}`, {
                headers: { Authorization: `Bearer ${token}` }
            });

            // Remove from local state
            setStories(stories.filter(s => s._id !== storyId));

            // Refresh stats
            fetchStats();
        } catch (error) {
            console.error('Error deleting story:', error);
        }
    };

    useEffect(() => {
        fetchStories(1);
        fetchStats();
    }, [filter, sortBy, sortOrder]);

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 py-8 px-4">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-gray-800 mb-2 flex items-center gap-3">
                        <Book className="text-purple-600" size={40} />
                        My Story Library
                    </h1>
                    {stats && (
                        <p className="text-gray-600">
                            {stats.total_stories} {stats.total_stories === 1 ? 'story' : 'stories'} • {stats.total_favorites} favorites
                        </p>
                    )}
                </div>

                {/* Search and Filters */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <form onSubmit={handleSearch} className="flex gap-4 mb-4">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-3 text-gray-400" size={20} />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search stories by title or prompt..."
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            />
                        </div>
                        <button
                            type="submit"
                            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                        >
                            Search
                        </button>
                    </form>

                    <div className="flex gap-4 flex-wrap">
                        {/* Filter */}
                        <select
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                        >
                            <option value="all">All Stories</option>
                            <option value="favorites">Favorites Only</option>
                        </select>

                        {/* Sort By */}
                        <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value)}
                            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                        >
                            <option value="created_at">Date Created</option>
                            <option value="title">Title</option>
                            <option value="view_count">Most Viewed</option>
                        </select>

                        {/* Sort Order */}
                        <select
                            value={sortOrder}
                            onChange={(e) => setSortOrder(e.target.value)}
                            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                        >
                            <option value="desc">Newest First</option>
                            <option value="asc">Oldest First</option>
                        </select>
                    </div>
                </div>

                {/* Stories Grid */}
                {loading ? (
                    <SkeletonLoader type="card" count={6} />
                ) : stories.length === 0 ? (
                    <div className="text-center py-16">
                        <Book size={64} className="mx-auto text-gray-300 mb-4" />
                        <h3 className="text-2xl font-semibold text-gray-600 mb-2">
                            {searchQuery ? 'No stories found' : 'No stories yet'}
                        </h3>
                        <p className="text-gray-500 mb-6">
                            {searchQuery
                                ? 'Try a different search term'
                                : 'Start creating your first story!'}
                        </p>
                        {!searchQuery && (
                            <button
                                onClick={() => navigate('/dashboard')}
                                className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                            >
                                Create Story
                            </button>
                        )}
                    </div>
                ) : (
                    <>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                            {stories.map((story) => (
                                <div
                                    key={story._id}
                                    className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow cursor-pointer"
                                >
                                    {/* Story Preview Image */}
                                    <div
                                        className="h-48 bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white text-6xl"
                                        onClick={() => navigate(`/story/${story._id}`)}
                                    >
                                        📚
                                    </div>

                                    <div className="p-4">
                                        {/* Title */}
                                        <h3
                                            className="text-lg font-semibold text-gray-800 mb-2 line-clamp-2 hover:text-purple-600 cursor-pointer"
                                            onClick={() => navigate(`/story/${story._id}`)}
                                        >
                                            {story.title}
                                        </h3>

                                        {/* Meta Info */}
                                        <div className="flex items-center gap-2 text-sm text-gray-500 mb-3">
                                            <Calendar size={14} />
                                            <span>{new Date(story.created_at).toLocaleDateString()}</span>
                                            <span>•</span>
                                            <span className="capitalize">{story.story_length}</span>
                                        </div>

                                        {/* Prompt Preview */}
                                        <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                                            {story.prompt}
                                        </p>

                                        {/* Actions */}
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => toggleFavorite(story._id, story.is_favorite)}
                                                className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg transition-colors ${story.is_favorite
                                                        ? 'bg-red-100 text-red-600 hover:bg-red-200'
                                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                                    }`}
                                            >
                                                <Heart size={16} fill={story.is_favorite ? 'currentColor' : 'none'} />
                                                {story.is_favorite ? 'Favorited' : 'Favorite'}
                                            </button>

                                            <button
                                                onClick={() => deleteStory(story._id)}
                                                className="px-3 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-red-100 hover:text-red-600 transition-colors"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Pagination */}
                        {pagination.total_pages > 1 && (
                            <div className="flex justify-center gap-2">
                                <button
                                    onClick={() => fetchStories(currentPage - 1)}
                                    disabled={!pagination.has_prev}
                                    className="px-4 py-2 bg-white rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                                >
                                    Previous
                                </button>
                                <span className="px-4 py-2 bg-white rounded-lg shadow">
                                    Page {pagination.page} of {pagination.total_pages}
                                </span>
                                <button
                                    onClick={() => fetchStories(currentPage + 1)}
                                    disabled={!pagination.has_next}
                                    className="px-4 py-2 bg-white rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                                >
                                    Next
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default Library;
