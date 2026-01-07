import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Download, Heart, Trash2, ArrowLeft, Book } from 'lucide-react';
import SkeletonLoader from '../components/SkeletonLoader';

const StoryDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [story, setStory] = useState(null);
    const [loading, setLoading] = useState(true);
    const [currentPage, setCurrentPage] = useState(0);

    useEffect(() => {
        fetchStory();
    }, [id]);

    const fetchStory = async () => {
        try {
            setLoading(true);
            const token = localStorage.getItem('token');
            const response = await axios.get(`/api/story/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setStory(response.data.story);
        } catch (error) {
            console.error('Error fetching story:', error);
        } finally {
            setLoading(false);
        }
    };

    const toggleFavorite = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await axios.patch(`/api/story/${id}/favorite`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setStory({ ...story, is_favorite: response.data.is_favorite });
        } catch (error) {
            console.error('Error toggling favorite:', error);
        }
    };

    const deleteStory = async () => {
        if (!confirm('Are you sure you want to delete this story? This cannot be undone.')) return;

        try {
            const token = localStorage.getItem('token');
            await axios.delete(`/api/story/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            navigate('/library');
        } catch (error) {
            console.error('Error deleting story:', error);
        }
    };

    const downloadPDF = () => {
        if (story?.pdf_file) {
            window.open(`/api/download-pdf/${story.story_id}`, '_blank');
        }
    };

    const downloadAudio = () => {
        if (story?.audio_files?.length > 0) {
            window.open(`/api/download-audiobook/${story.story_id}`, '_blank');
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 py-8 px-4">
                <div className="max-w-4xl mx-auto">
                    <SkeletonLoader type="page" count={1} />
                </div>
            </div>
        );
    }

    if (!story) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 py-8 px-4">
                <div className="max-w-4xl mx-auto text-center">
                    <h2 className="text-2xl font-bold text-gray-800 mb-4">Story Not Found</h2>
                    <button
                        onClick={() => navigate('/library')}
                        className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                    >
                        Back to Library
                    </button>
                </div>
            </div>
        );
    }

    const pages = story.story_data?.pages || [];
    const currentStoryPage = pages[currentPage];

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 py-8 px-4">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="flex justify-between items-start mb-6">
                    <button
                        onClick={() => navigate('/library')}
                        className="flex items-center gap-2 text-gray-600 hover:text-gray-800"
                    >
                        <ArrowLeft size={20} />
                        Back to Library
                    </button>

                    <div className="flex gap-2">
                        <button
                            onClick={toggleFavorite}
                            className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${story.is_favorite
                                ? 'bg-red-100 text-red-600 hover:bg-red-200'
                                : 'bg-white text-gray-600 hover:bg-gray-100'
                                }`}
                        >
                            <Heart size={18} fill={story.is_favorite ? 'currentColor' : 'none'} />
                            {story.is_favorite ? 'Favorited' : 'Favorite'}
                        </button>

                        <button
                            onClick={deleteStory}
                            className="px-4 py-2 bg-white text-gray-600 rounded-lg hover:bg-red-100 hover:text-red-600 transition-colors"
                        >
                            <Trash2 size={18} />
                        </button>
                    </div>
                </div>

                {/* Story Info Card */}
                <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
                    <h1 className="text-3xl font-bold text-gray-800 mb-2">{story.title}</h1>

                    <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-4">
                        <span className="flex items-center gap-2">
                            <Book size={16} />
                            {pages.length} pages
                        </span>
                        <span>•</span>
                        <span className="capitalize">{story.story_length} story</span>
                        <span>•</span>
                        <span>{new Date(story.created_at).toLocaleDateString()}</span>
                        <span>•</span>
                        <span>{story.view_count} views</span>
                    </div>

                    {story.prompt && (
                        <div className="bg-purple-50 rounded-lg p-4 mb-4">
                            <div className="text-sm text-purple-700 font-semibold mb-1">Original Prompt</div>
                            <div className="text-gray-700">{story.prompt}</div>
                        </div>
                    )}

                    {/* Download Buttons */}
                    <div className="flex gap-3">
                        {story.pdf_file && (
                            <button
                                onClick={downloadPDF}
                                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                            >
                                <Download size={18} />
                                Download PDF
                            </button>
                        )}
                        {story.audio_files && story.audio_files.length > 0 && (
                            <button
                                onClick={downloadAudio}
                                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                <Download size={18} />
                                Download Audio
                            </button>
                        )}
                    </div>
                </div>

                {/* Story Pages */}
                <div className="bg-white rounded-lg shadow-lg p-8">
                    {currentStoryPage && (
                        <div className="space-y-6">
                            {/* Page Image */}
                            {story.image_files && story.image_files[currentPage] && (
                                <div className="flex justify-center">
                                    <img
                                        src={`/api/download/${story.image_files[currentPage]}`}
                                        alt={`Page ${currentPage + 1}`}
                                        className="max-w-full h-auto rounded-lg shadow-md"
                                        onError={(e) => {
                                            e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect fill="%23f3f4f6" width="400" height="300"/><text x="50%" y="50%" font-size="20" fill="%236b7280" text-anchor="middle">Image not available</text></svg>';
                                        }}
                                    />
                                </div>
                            )}

                            {/* Page Text */}
                            <div className="text-center">
                                <p className="text-xl text-gray-800 leading-relaxed">
                                    {currentStoryPage.text}
                                </p>
                            </div>

                            {/* Page Number */}
                            <div className="text-center text-gray-500 text-sm">
                                Page {currentPage + 1} of {pages.length}
                            </div>

                            {/* Navigation */}
                            <div className="flex justify-between items-center pt-6 border-t">
                                <button
                                    onClick={() => setCurrentPage(currentPage - 1)}
                                    disabled={currentPage === 0}
                                    className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    Previous
                                </button>

                                <div className="flex gap-2">
                                    {pages.map((_, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => setCurrentPage(idx)}
                                            className={`w-3 h-3 rounded-full transition-colors ${idx === currentPage ? 'bg-purple-600' : 'bg-gray-300 hover:bg-gray-400'
                                                }`}
                                            aria-label={`Go to page ${idx + 1}`}
                                        />
                                    ))}
                                </div>

                                <button
                                    onClick={() => setCurrentPage(currentPage + 1)}
                                    disabled={currentPage === pages.length - 1}
                                    className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    Next
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Story Info (if available) */}
                {story.story_data && (
                    <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                        {story.story_data.character_description && (
                            <div className="bg-white rounded-lg shadow p-4">
                                <h3 className="font-semibold text-gray-800 mb-2">Character</h3>
                                <p className="text-gray-600 text-sm">{story.story_data.character_description}</p>
                            </div>
                        )}
                        {story.story_data.setting && (
                            <div className="bg-white rounded-lg shadow p-4">
                                <h3 className="font-semibold text-gray-800 mb-2">Setting</h3>
                                <p className="text-gray-600 text-sm">{story.story_data.setting}</p>
                            </div>
                        )}
                        {story.story_data.moral && (
                            <div className="bg-white rounded-lg shadow p-4 md:col-span-2">
                                <h3 className="font-semibold text-gray-800 mb-2">Moral of the Story</h3>
                                <p className="text-gray-600 text-sm">{story.story_data.moral}</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default StoryDetail;
