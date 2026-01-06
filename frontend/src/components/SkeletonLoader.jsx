import React from 'react';

const SkeletonLoader = ({ type = 'page', count = 1 }) => {
    const PageSkeleton = () => (
        <div className="animate-pulse space-y-4 mb-6">
            {/* Image skeleton */}
            <div className="bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 bg-[length:200%_100%] animate-shimmer h-64 rounded-lg" />

            {/* Text skeleton */}
            <div className="space-y-3">
                <div className="h-4 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 bg-[length:200%_100%] animate-shimmer rounded w-3/4" />
                <div className="h-4 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 bg-[length:200%_100%] animate-shimmer rounded w-5/6" />
                <div className="h-4 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 bg-[length:200%_100%] animate-shimmer rounded w-4/5" />
            </div>

            {/* Page number */}
            <div className="flex justify-center">
                <div className="h-6 w-12 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 bg-[length:200%_100%] animate-shimmer rounded" />
            </div>
        </div>
    );

    const CardSkeleton = () => (
        <div className="animate-pulse">
            <div className="bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 bg-[length:200%_100%] animate-shimmer h-48 rounded-lg mb-4" />
            <div className="h-4 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 bg-[length:200%_100%] animate-shimmer rounded w-2/3 mb-2" />
            <div className="h-3 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 bg-[length:200%_100%] animate-shimmer rounded w-1/2" />
        </div>
    );

    const items = Array.from({ length: count }, (_, i) => (
        <div key={i}>
            {type === 'page' ? <PageSkeleton /> : <CardSkeleton />}
        </div>
    ));

    return <div className="space-y-6">{items}</div>;
};

export default SkeletonLoader;
