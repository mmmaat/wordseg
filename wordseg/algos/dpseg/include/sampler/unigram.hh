#ifndef _SAMPLER_UNIGRAM_H
#define _SAMPLER_UNIGRAM_H

#include "sampler/base.hh"


namespace sampler
{
    class unigram: public base
    {
    public:
        unigram(const parameters& params, const data::data& constants, const annealing& anneal);
        virtual ~unigram();
        virtual bool sanity_check() const;
        virtual double log_posterior() const;
        virtual std::vector<double> predict_pairs(
            const std::vector<std::pair<substring, substring> >& test_pairs) const;
        virtual void print_lexicon(std::wostream& os) const;

        virtual void estimate(uint iters, std::wostream& os, uint eval_iters = 0,
            double temperature = 1, bool maximize = false, bool is_decayed = false) = 0;

    protected:
        Unigrams m_lex;

        virtual void print_statistics(std::wostream& os, uint iters, double temp, bool do_header=false);
        virtual std::vector<bool> hypersample(double temperature);
        virtual void estimate_sentence(Sentence& s, double temperature) = 0;
        virtual void estimate_eval_sentence(Sentence& s, double temperature, bool maximize = false);
    };


    class batch_unigram: public unigram
    {
    public:
        batch_unigram(const parameters& params, const data::data& constants, const annealing& anneal);
        virtual ~batch_unigram();
        virtual void estimate(uint iters, std::wostream& os, uint eval_iters = 0,
            double temperature = 1, bool maximize = false, bool is_decayed = false);

    protected:
        virtual void estimate_sentence(Sentence& s, double temperature) = 0;
    };


    class online_unigram: public unigram
    {
    public:
        online_unigram(
            const parameters& params, const data::data& constants, const annealing& anneal, double forget_rate = 0);
        virtual ~online_unigram();
        virtual void estimate(
            uint iters, std::wostream& os, uint eval_iters = 0,
            double temperature = 1, bool maximize = false, bool is_decayed = false);

    protected:
        double _forget_rate;
        Sentences _sentences_seen; // for use with DeacyedMCMC model in particular
        virtual void estimate_sentence(Sentence& s, double temperature) = 0;
        void forget_items(Sentences::iterator i);
    };
}


#endif  // _SAMPLER_UNIGRAM_H
