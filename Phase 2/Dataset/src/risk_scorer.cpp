// Member-1: Risk scorer (C++ OOP submission version — mirrors scripts/risk_scorer.py)
// Classes: Location, DynamicFeatures, RiskProfile, BaseScorer (abstract) -> WeightedRiskScorer, CsvHandler
// Run from project root:  g++ -std=c++17 src/risk_scorer.cpp -o risk_scorer && ./risk_scorer
// Reads:  data/locations_static.csv, data/dynamic_features.csv   (config/risk_weights.json values mirrored below)
// Writes: data/risk_scores.csv, data/risk_output.json  (same handoff contract as Python version)

#include <algorithm>
#include <cctype>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

// ---------- weights (mirror config/risk_weights.json) ----------
namespace Weights {
constexpr double STATIC_W = 0.6, DYNAMIC_W = 0.4;
constexpr double W_SLOPE = 0.30, W_HIST = 0.20, W_SOIL = 0.15;
constexpr double W_LAND = 0.12, W_LITH = 0.13, W_ROAD = 0.10;
constexpr double W_CUR = 0.45, W_FC = 0.35, W_MOIST = 0.20;
constexpr double SLOPE_MAX = 70.0, HIST_CAP = 50.0, RAIN_CAP = 100.0;
constexpr double LOW_MAX = 25.0, MOD_MAX = 50.0, HIGH_MAX = 75.0;
}

static std::string trim(const std::string& s) {
    size_t a = s.find_first_not_of(" \t\r\n\"");
    if (a == std::string::npos) return "";
    size_t b = s.find_last_not_of(" \t\r\n\"");
    return s.substr(a, b - a + 1);
}
static std::string lower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return std::tolower(c); });
    return s;
}
static std::vector<std::string> splitCsv(const std::string& line) {
    std::vector<std::string> out;
    std::string cur;
    bool inQ = false;
    for (char c : line) {
        if (c == '"') inQ = !inQ;
        else if (c == ',' && !inQ) { out.push_back(trim(cur)); cur.clear(); }
        else cur += c;
    }
    out.push_back(trim(cur));
    return out;
}
static double clamp01(double v) { return v < 0 ? 0 : (v > 1 ? 1 : v); }

// ---------- Location (encapsulated static features) ----------
class Location {
private:
    std::string id_, name_, soil_, landuse_, road_;
    double lat_, lon_, elev_, slope_, lith_;
    int hist_;

public:
    Location(std::string id, std::string name, double lat, double lon,
             double elev, double slope, std::string soil, std::string landuse,
             double lith, int hist, std::string road)
        : id_(id), name_(name), lat_(lat), lon_(lon), elev_(elev), slope_(slope),
          soil_(soil), landuse_(landuse), lith_(lith), hist_(hist), road_(road) {}

    const std::string& id() const { return id_; }
    const std::string& name() const { return name_; }
    double lat() const { return lat_; }
    double lon() const { return lon_; }
    double slope() const { return slope_; }
    int history() const { return hist_; }
    double lithology() const { return lith_; }

    double soilFactor() const {
        std::string s = lower(soil_);
        if (s == "sandy") return 0.4;
        if (s == "silt") return 0.55;
        if (s == "rocky") return 0.85;
        return 0.7; // loamy (default)
    }
    double landuseFactor() const {
        std::string s = lower(landuse_);
        if (s == "dense-forest") return 0.27;
        if (s == "open-forest") return 0.45;
        if (s == "scrub") return 0.5;
        return 0.99; // non-forest
    }
    double roadFactor() const {
        std::string s = lower(road_);
        if (s == "good") return 0.2;
        if (s == "poor") return 0.9;
        return 0.5; // moderate
    }
};

struct DynamicFeatures {
    std::string id;
    double currentRain = 0, forecast24 = 0, antecedent3d = 0, humidity = 50;
};

// ---------- RiskProfile (encapsulated result) ----------
class RiskProfile {
private:
    double staticScore_ = 0, dynamicScore_ = 0, totalScore_ = 0;
    std::string level_ = "Low";

public:
    void setScores(double s, double d, double t) {
        staticScore_ = s; dynamicScore_ = d; totalScore_ = t;
        level_ = (t < Weights::LOW_MAX) ? "Low"
               : (t < Weights::MOD_MAX) ? "Moderate"
               : (t < Weights::HIGH_MAX) ? "High" : "Critical";
    }
    double staticScore() const { return staticScore_; }
    double dynamicScore() const { return dynamicScore_; }
    double totalScore() const { return totalScore_; }
    const std::string& level() const { return level_; }
};

// ---------- Scorer hierarchy (inheritance) ----------
class BaseScorer {
public:
    virtual ~BaseScorer() = default;
    virtual double computeStatic(const Location& l) const = 0;
    virtual double computeDynamic(const DynamicFeatures& d) const = 0;
};

class WeightedRiskScorer : public BaseScorer {
public:
    double computeStatic(const Location& l) const override {
        double slopeN = clamp01(l.slope() / Weights::SLOPE_MAX);
        double histN = clamp01(l.history() / Weights::HIST_CAP);
        double s = Weights::W_SLOPE * slopeN + Weights::W_HIST * histN +
                   Weights::W_SOIL * l.soilFactor() + Weights::W_LAND * l.landuseFactor() +
                   Weights::W_LITH * clamp01(l.lithology()) + Weights::W_ROAD * l.roadFactor();
        return std::round(s * 10000.0) / 100.0;
    }
    double computeDynamic(const DynamicFeatures& d) const override {
        double cur = clamp01(d.currentRain / Weights::RAIN_CAP);
        double fc = clamp01(d.forecast24 / Weights::RAIN_CAP);
        double ant = clamp01(d.antecedent3d / Weights::RAIN_CAP);
        double hum = clamp01(d.humidity / 100.0);
        double moist = 0.6 * ant + 0.4 * hum; // soil-moisture proxy (OWM has no soil field)
        double s = Weights::W_CUR * cur + Weights::W_FC * fc + Weights::W_MOIST * moist;
        return std::round(s * 10000.0) / 100.0;
    }
    double computeTotal(double s, double d) const {
        return std::round((Weights::STATIC_W * s + Weights::DYNAMIC_W * d) * 100.0) / 100.0;
    }
};

// ---------- CSV / JSON file handling ----------
class CsvHandler {
public:
    static std::vector<Location> readStatic(const std::string& path) {
        std::vector<Location> out;
        std::ifstream f(path);
        if (!f) throw std::runtime_error("Cannot open " + path +
            " (run from project root)");
        std::string line;
        std::getline(f, line); // header
        while (std::getline(f, line)) {
            if (line.empty()) continue;
            auto c = splitCsv(line);
            if (c.size() < 12) continue;
            out.emplace_back(c[0], c[1], std::stod(c[2]), std::stod(c[3]),
                             std::stod(c[4]), std::stod(c[5]), c[7], c[8],
                             std::stod(c[9]), std::stoi(c[10]), c[11]);
        }
        return out;
    }
    static std::map<std::string, DynamicFeatures> readDynamic(const std::string& path) {
        std::map<std::string, DynamicFeatures> m;
        std::ifstream f(path);
        if (!f) throw std::runtime_error("Cannot open " + path +
            " (run scripts/fetch_weather.py --mock first)");
        std::string line;
        std::getline(f, line);
        while (std::getline(f, line)) {
            if (line.empty()) continue;
            auto c = splitCsv(line);
            if (c.size() < 6) continue;
            DynamicFeatures d;
            d.id = c[0];
            d.currentRain = std::stod(c[1]);
            d.forecast24 = std::stod(c[2]);
            d.humidity = std::stod(c[4]);
            d.antecedent3d = std::stod(c[5]);
            m[d.id] = d;
        }
        return m;
    }
};

int main() {
    try {
        auto locs = CsvHandler::readStatic("data/locations_static.csv");
        auto dyn = CsvHandler::readDynamic("data/dynamic_features.csv");
        WeightedRiskScorer scorer;

        struct Row { const Location* loc; DynamicFeatures d; RiskProfile p; };
        std::vector<Row> rows;
        for (auto& l : locs) {
            auto it = dyn.find(l.id());
            if (it == dyn.end()) {
                std::cerr << "[warn] " << l.id() << " has no dynamic row -> skipped\n";
                continue;
            }
            RiskProfile p;
            double s = scorer.computeStatic(l);
            double d = scorer.computeDynamic(it->second);
            p.setScores(s, d, scorer.computeTotal(s, d));
            rows.push_back({&l, it->second, p});
        }
        std::sort(rows.begin(), rows.end(), [](const Row& a, const Row& b) {
            return a.p.totalScore() > b.p.totalScore();
        });

        std::ofstream csv("data/risk_scores.csv");
        csv << "location_id,name,lat,lon,static_score,dynamic_score,total_score,"
               "risk_level,current_rain_mm,forecast_24h_mm,humidity_pct\n";
        for (auto& r : rows) {
            csv << r.loc->id() << "," << r.loc->name() << "," << r.loc->lat() << ","
                << r.loc->lon() << "," << std::fixed << std::setprecision(2)
                << r.p.staticScore() << "," << r.p.dynamicScore() << ","
                << r.p.totalScore() << "," << r.p.level() << ","
                << r.d.currentRain << "," << r.d.forecast24 << ","
                << (int)r.d.humidity << "\n";
        }

        std::ofstream js("data/risk_output.json");
        js << "{\n  \"generator\": \"risk_scorer.cpp (OOP)\",\n  \"locations\": [\n";
        for (size_t i = 0; i < rows.size(); ++i) {
            auto& r = rows[i];
            js << "    {\"location_id\": \"" << r.loc->id() << "\", \"name\": \""
               << r.loc->name() << "\", \"lat\": " << r.loc->lat()
               << ", \"lon\": " << r.loc->lon() << ", \"static_score\": "
               << std::fixed << std::setprecision(2) << r.p.staticScore()
               << ", \"dynamic_score\": " << r.p.dynamicScore()
               << ", \"total_score\": " << r.p.totalScore()
               << ", \"risk_level\": \"" << r.p.level() << "\"}"
               << (i + 1 < rows.size() ? ",\n" : "\n");
        }
        js << "  ]\n}\n";

        std::cout << "Scored " << rows.size()
                  << " locations -> data/risk_scores.csv, data/risk_output.json\n";
        for (auto& r : rows) {
            std::cout << "  " << r.loc->id() << " static=" << r.p.staticScore()
                      << " dynamic=" << r.p.dynamicScore()
                      << " total=" << r.p.totalScore() << " " << r.p.level() << "\n";
        }
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "ERROR: " << e.what() << "\n";
        return 1;
    }
}
