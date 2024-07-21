import React, { useState, useEffect } from 'react';
import axios from 'axios';



const Spinner = () => (
    <div className="flex justify-center items-center">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
    </div>
  );
  
  const Modal = ({ isOpen, onClose, title, content, isLoading }) => {
    if (!isOpen) return null;
  
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center">
        <div className="bg-white p-6 rounded-lg max-w-[36rem] w-full">
          <h2 className="text-xl font-bold mb-4">{title}</h2>
          <div className="bg-gray-100 p-4 rounded mb-4 min-h-[100px] max-h-[500px] flex items-center justify-center overflow-y-auto">
            {isLoading ? <Spinner /> : <p>{content}</p>}
          </div>
          <button 
            onClick={onClose}
            className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded"
          >
            Close
          </button>
        </div>
      </div>
    );
  };

const FactCheckUI = ({ title, subtitle }) => {
  const [speaker1Facts, setSpeaker1Facts] = useState([]);
  const [speaker2Facts, setSpeaker2Facts] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);


  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/fact-check');

        if (response.data === "NO FACTS FOUND")
        {
            return;
        }


        //loop over all new facts and add them to the correct speaker
        response.data.forEach(element => {
            if (element.speaker === 'spk_1') {
                setSpeaker1Facts(prevFacts => [element, ...prevFacts]);
            } else if (element.speaker === 'spk_2') {
                setSpeaker2Facts(prevFacts => [element, ...prevFacts]);
            }
        });

        
      } catch (error) {
        console.error('Error fetching fact-check data:', error);
      }
    };

    const intervalId = setInterval(fetchData, 1000);

    return () => clearInterval(intervalId);
  }, []);

  
  const doubleCheck = async (factState, fact, factCorrection) => {
    setIsLoading(true);
    setModalContent('');
    setIsModalOpen(true);

    const data = {
      fact_state: factState,
      fact: fact,
      fact_correction: factCorrection
    };

    try {
      const response = await axios.post('http://localhost:5000/api/multion', data, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      console.log('Success:', response);
      setModalContent(response.data);
    } catch (error) {
      console.error('Error:', error);
      setModalContent('An error occurred while double checking.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderFact = (fact) => {
    let color;
    switch (fact.fact_state) {
      case 0:
        color = 'text-red-600';
        break;
      case 1:
        color = 'text-red-600';
        break;
      case 2:
        color = 'text-green-600';
        break;
      default:
        color = 'text-gray-700';
    }

    return (
      <div onClick={() => doubleCheck(fact.fact_state, fact.fact, fact.fact_correction)}  key={Math.random()} className={`mb-2 ${color}`}>
        <p >{fact.fact}</p>
        {fact.fact_state < 2 && (
          <p className="text-sm italic">Correction: {fact.fact_correction}</p>
        )}
      </div>
    );
  };

  const resetFacts = () => {
    setSpeaker1Facts([]);
    setSpeaker2Facts([]);
  };

  return (
    
    <div className="min-h-screen bg-gray-100 p-8">
        <Modal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        title="Double Check" 
        content={modalContent}
        isLoading={isLoading}
      />
      <div className="max-w-6xl mx-auto bg-white rounded-lg shadow-md overflow-hidden">
        <div className="p-6">
          <h1 className="text-3xl font-bold text-center text-gray-800">{title}</h1>
          <h2 className="text-xl text-center text-gray-600 mt-2">{subtitle}</h2>
        </div>
        
        <div className="flex flex-col md:flex-row">
          <div className="flex-1 p-6 border-b md:border-b-0 md:border-r border-gray-200">
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Speaker 1</h3>
            <div className="bg-gray-50 p-4 rounded-lg h-[22rem] overflow-y-auto">
              {speaker1Facts.map(renderFact)}
            </div>
          </div>
          
          <div className="flex-1 p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Speaker 2</h3>
            <div className="bg-gray-50 p-4 rounded-lg h-[22rem] overflow-y-auto">
              {speaker2Facts.map(renderFact)}
            </div>
          </div>
        </div>
        
        <div className="p-4 text-center">
            <h4 className="text-md text-center text-gray-600 mt-2 mb-2">Click on any fact to doble check it using MultiOn</h4>
          <button 
            onClick={resetFacts}
            className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-300"
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  );
};

export default FactCheckUI;