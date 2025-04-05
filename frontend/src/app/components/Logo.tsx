'use client';

export default function Logo() {
  return (
    <div className="flex items-center">
      <div className="mr-2 bg-blue-600 text-white rounded-lg p-2">
        <svg 
          width="24" 
          height="24" 
          viewBox="0 0 24 24" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <path 
            d="M9 7L9 2M15 7V2M11 13H13M7 11V13H9V11H7ZM7 11V9H9V11M15 11V13H17V11H15ZM15 11V9H17V11M7 17V19H9V17H7ZM7 17V15H9V17M15 17V19H17V17H15ZM15 17V15H17V17" 
            stroke="currentColor" 
            strokeWidth="2" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          />
          <path 
            d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" 
            stroke="currentColor" 
            strokeWidth="2"
          />
        </svg>
      </div>
      <h1 className="text-2xl font-bold text-gray-900">Askit</h1>
    </div>
  );
}